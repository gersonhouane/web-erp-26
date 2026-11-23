"""Registo, login e tokens.

Estas operações correm com RLS em modo de sistema (`bypass`), porque acontecem antes
de existir uma empresa activa. Cada função limita-se ao utilizador em causa.
"""

import uuid
from datetime import UTC, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.db import rls_bypass, set_rls_context
from app.core.errors import Forbidden, Unauthorized
from app.core.security import (
    create_access_token,
    hash_refresh_token,
    new_refresh_token,
    verify_password,
)
from app.modules.auth.schemas import SignupIn, TokenOut
from app.modules.core.models import Company, Tenant
from app.modules.core.service import create_company
from app.modules.users.models import RefreshToken, User, UserCompanyRole
from app.modules.users.service import create_user
from app.shared import audit

_INVALID = ("INVALID_CREDENTIALS", "E-mail ou senha incorrectos.")


def _now() -> datetime:
    return datetime.now(UTC)


def issue_tokens(db: Session, user: User, company_id: uuid.UUID | None) -> TokenOut:
    settings = get_settings()
    raw, token_hash = new_refresh_token()
    db.add(
        RefreshToken(
            user_id=user.id,
            token_hash=token_hash,
            company_id=company_id,
            expires_at=_now() + timedelta(days=settings.refresh_token_days),
        )
    )
    access = create_access_token(user_id=user.id, tenant_id=user.tenant_id, company_id=company_id)
    return TokenOut(
        access_token=access,
        refresh_token=raw,
        expires_in=settings.access_token_minutes * 60,
        company_id=company_id,
    )


def default_company(db: Session, user: User) -> uuid.UUID | None:
    return db.scalar(
        select(UserCompanyRole.company_id)
        .join(Company, Company.id == UserCompanyRole.company_id)
        .where(UserCompanyRole.user_id == user.id, Company.is_active.is_(True))
        .order_by(UserCompanyRole.created_at)
        .limit(1)
    )


def signup(db: Session, data: SignupIn, ip: str | None) -> TokenOut:
    set_rls_context(db, bypass=True)
    tenant = Tenant(name=data.organization_name)
    db.add(tenant)
    db.flush()
    user = create_user(
        db, tenant_id=tenant.id, name=data.name, email=data.email, password=data.password
    )
    company = create_company(db, tenant_id=tenant.id, data=data.company, owner=user)
    audit.record(
        db,
        tenant_id=tenant.id,
        company_id=company.id,
        user_id=user.id,
        action="signup",
        entity="tenant",
        entity_id=tenant.id,
        after={"organization": tenant.name, "company": company.name},
        ip=ip,
    )
    tokens = issue_tokens(db, user, company.id)
    db.commit()
    return tokens


def login(db: Session, email: str, password: str, ip: str | None) -> TokenOut:
    settings = get_settings()
    set_rls_context(db, bypass=True)
    user = db.scalar(select(User).where(User.email == email.lower()))
    if user is None or not user.is_active:
        raise Unauthorized(*_INVALID)
    if user.locked_until and user.locked_until > _now():
        raise Unauthorized(
            "ACCOUNT_LOCKED",
            "Conta bloqueada temporariamente por tentativas falhadas.",
            details={"locked_until": user.locked_until.isoformat()},
        )
    if not verify_password(password, user.password_hash):
        user.failed_logins += 1
        if user.failed_logins >= settings.max_failed_logins:
            user.locked_until = _now() + timedelta(minutes=settings.lockout_minutes)
            user.failed_logins = 0
        db.commit()
        raise Unauthorized(*_INVALID)

    user.failed_logins = 0
    user.locked_until = None
    user.last_login_at = _now()
    company_id = default_company(db, user)
    audit.record(
        db,
        tenant_id=user.tenant_id,
        company_id=company_id,
        user_id=user.id,
        action="login",
        entity="user",
        entity_id=user.id,
        ip=ip,
    )
    tokens = issue_tokens(db, user, company_id)
    db.commit()
    return tokens


def refresh(db: Session, raw_token: str) -> TokenOut:
    """Roda o refresh token: o antigo é revogado e é emitido um novo par."""
    set_rls_context(db, bypass=True)
    stored = db.scalar(
        select(RefreshToken).where(RefreshToken.token_hash == hash_refresh_token(raw_token))
    )
    if stored is None or stored.expires_at <= _now():
        raise Unauthorized("INVALID_REFRESH_TOKEN", "Sessão expirada. Entre de novo.")
    if stored.revoked_at is not None:
        # Reutilização de um token já rodado: possível roubo. Revoga todos os do utilizador.
        _revoke_all(db, stored.user_id)
        db.commit()
        raise Unauthorized("INVALID_REFRESH_TOKEN", "Sessão expirada. Entre de novo.")
    user = db.get(User, stored.user_id)
    if user is None or not user.is_active:
        raise Unauthorized("INVALID_REFRESH_TOKEN", "Sessão expirada. Entre de novo.")
    stored.revoked_at = _now()
    company_id = stored.company_id if _has_access(db, user, stored.company_id) else None
    tokens = issue_tokens(db, user, company_id or default_company(db, user))
    db.commit()
    return tokens


def logout(db: Session, raw_token: str) -> None:
    set_rls_context(db, bypass=True)
    stored = db.scalar(
        select(RefreshToken).where(RefreshToken.token_hash == hash_refresh_token(raw_token))
    )
    if stored and stored.revoked_at is None:
        stored.revoked_at = _now()
        db.commit()


def switch_company(db: Session, user: User, company_id: uuid.UUID) -> TokenOut:
    with rls_bypass(db):
        allowed = _has_access(db, user, company_id)
    if not allowed:
        raise Forbidden("COMPANY_ACCESS_DENIED", "Não tem acesso a esta empresa.")
    tokens = issue_tokens(db, user, company_id)
    db.commit()
    return tokens


def user_companies(db: Session, user: User) -> list[tuple[Company, str]]:
    with rls_bypass(db):
        rows = db.execute(
            select(Company, UserCompanyRole)
            .join(UserCompanyRole, UserCompanyRole.company_id == Company.id)
            .where(UserCompanyRole.user_id == user.id, Company.is_active.is_(True))
            .order_by(Company.name)
        ).all()
        return [(company, link.role.name) for company, link in rows]


def _has_access(db: Session, user: User, company_id: uuid.UUID | None) -> bool:
    if company_id is None:
        return False
    return (
        db.scalar(
            select(UserCompanyRole.id)
            .join(Company, Company.id == UserCompanyRole.company_id)
            .where(
                UserCompanyRole.user_id == user.id,
                UserCompanyRole.company_id == company_id,
                Company.tenant_id == user.tenant_id,
                Company.is_active.is_(True),
            )
        )
        is not None
    )


def _revoke_all(db: Session, user_id: uuid.UUID) -> None:
    for token in db.scalars(
        select(RefreshToken).where(
            RefreshToken.user_id == user_id, RefreshToken.revoked_at.is_(None)
        )
    ):
        token.revoked_at = _now()
