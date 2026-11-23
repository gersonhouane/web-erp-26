"""Dependências FastAPI: sessão com contexto RLS, utilizador actual e permissões."""

import uuid
from collections.abc import Callable, Iterator
from dataclasses import dataclass, field

import jwt
from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.db import SessionLocal, set_rls_context
from app.core.errors import Forbidden, Unauthorized
from app.core.security import decode_access_token
from app.modules.users.models import User
from app.modules.users.service import permissions_for

_bearer = HTTPBearer(auto_error=False)


def get_db() -> Iterator[Session]:
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


@dataclass
class CurrentUser:
    user: User
    tenant_id: uuid.UUID
    company_id: uuid.UUID | None
    permissions: set[str] = field(default_factory=set)
    ip: str | None = None

    @property
    def id(self) -> uuid.UUID:
        return self.user.id

    def require_company(self) -> uuid.UUID:
        if self.company_id is None:
            raise Forbidden("NO_COMPANY", "Escolha uma empresa primeiro.")
        return self.company_id


def get_current_user(
    request: Request,
    creds: HTTPAuthorizationCredentials | None = Depends(_bearer),
    db: Session = Depends(get_db),
) -> CurrentUser:
    if creds is None:
        raise Unauthorized("NOT_AUTHENTICATED", "Sessão em falta.")
    try:
        payload = decode_access_token(creds.credentials)
        user_id = uuid.UUID(payload["sub"])
        tenant_id = uuid.UUID(payload["tid"])
        company_id = uuid.UUID(payload["cid"]) if payload.get("cid") else None
    except (jwt.PyJWTError, KeyError, ValueError) as exc:
        raise Unauthorized("INVALID_TOKEN", "Sessão inválida ou expirada.") from exc

    set_rls_context(db, tenant_id=tenant_id, company_id=company_id)
    user = db.get(User, user_id)
    if user is None or not user.is_active or user.tenant_id != tenant_id:
        raise Unauthorized("INVALID_TOKEN", "Sessão inválida ou expirada.")
    perms = permissions_for(db, user_id=user.id, company_id=company_id) if company_id else set()
    client = request.client.host if request.client else None
    return CurrentUser(user, tenant_id, company_id, perms, client)


def require_permission(code: str) -> Callable[..., CurrentUser]:
    def _check(current: CurrentUser = Depends(get_current_user)) -> CurrentUser:
        current.require_company()
        if code not in current.permissions:
            raise Forbidden("PERMISSION_DENIED", "Não tem permissão para esta acção.", details=code)
        return current

    return _check
