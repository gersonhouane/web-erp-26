import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.errors import Conflict, NotFound
from app.core.security import hash_password
from app.modules.users.models import Role, RolePermission, User, UserCompanyRole
from app.shared.permissions import PERMISSIONS, SYSTEM_ROLES, expand


def create_system_roles(db: Session, *, tenant_id: uuid.UUID, company_id: uuid.UUID) -> dict:
    """Cria os papéis padrão numa empresa nova. Devolve {nome: Role}."""
    roles = {}
    for name, (description, patterns) in SYSTEM_ROLES.items():
        role = Role(
            tenant_id=tenant_id,
            company_id=company_id,
            name=name,
            description=description,
            is_system=True,
        )
        role.permissions = [
            RolePermission(tenant_id=tenant_id, company_id=company_id, code=code)
            for code in sorted(expand(patterns))
        ]
        db.add(role)
        roles[name] = role
    db.flush()
    return roles


def assign_role(db: Session, *, user: User, company_id: uuid.UUID, role: Role) -> UserCompanyRole:
    link = db.scalar(
        select(UserCompanyRole).where(
            UserCompanyRole.user_id == user.id, UserCompanyRole.company_id == company_id
        )
    )
    if link is None:
        link = UserCompanyRole(
            tenant_id=user.tenant_id, company_id=company_id, user_id=user.id, role_id=role.id
        )
        db.add(link)
    else:
        link.role_id = role.id
    db.flush()
    return link


def permissions_for(db: Session, *, user_id: uuid.UUID, company_id: uuid.UUID) -> set[str]:
    rows = db.scalars(
        select(RolePermission.code)
        .join(UserCompanyRole, UserCompanyRole.role_id == RolePermission.role_id)
        .where(UserCompanyRole.user_id == user_id, UserCompanyRole.company_id == company_id)
    )
    return set(rows)


def get_role(db: Session, role_id: uuid.UUID) -> Role:
    role = db.get(Role, role_id)
    if role is None:  # RLS esconde papéis de outras empresas
        raise NotFound("ROLE_NOT_FOUND", "Papel não encontrado.")
    return role


def create_role(
    db: Session,
    *,
    tenant_id: uuid.UUID,
    company_id: uuid.UUID,
    name: str,
    description: str | None,
    codes: list[str],
) -> Role:
    unknown = sorted(set(codes) - PERMISSIONS.keys())
    if unknown:
        raise NotFound("PERMISSION_NOT_FOUND", "Permissões desconhecidas.", details=unknown)
    if db.scalar(select(Role).where(Role.company_id == company_id, Role.name == name)):
        raise Conflict("ROLE_EXISTS", "Já existe um papel com esse nome.")
    role = Role(tenant_id=tenant_id, company_id=company_id, name=name, description=description)
    role.permissions = [
        RolePermission(tenant_id=tenant_id, company_id=company_id, code=c) for c in set(codes)
    ]
    db.add(role)
    db.flush()
    return role


def create_user(db: Session, *, tenant_id: uuid.UUID, name: str, email: str, password: str) -> User:
    email = email.lower()
    if db.scalar(select(User.id).where(User.email == email)):
        raise Conflict("EMAIL_IN_USE", "Este e-mail já está registado.")
    user = User(tenant_id=tenant_id, name=name, email=email, password_hash=hash_password(password))
    db.add(user)
    db.flush()
    return user
