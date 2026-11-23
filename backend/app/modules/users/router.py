import uuid

from fastapi import APIRouter, Depends, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.deps import CurrentUser, get_db, require_permission
from app.core.errors import NotFound
from app.modules.users import service
from app.modules.users.models import Role, User, UserCompanyRole
from app.modules.users.schemas import (
    CompanyUserOut,
    PermissionOut,
    RoleCreate,
    RoleOut,
    UserInvite,
    UserRoleUpdate,
)
from app.shared import audit
from app.shared.permissions import PERMISSIONS

router = APIRouter(tags=["users"])


def _company_user(user: User, link: UserCompanyRole) -> CompanyUserOut:
    return CompanyUserOut(
        id=user.id,
        name=user.name,
        email=user.email,
        is_active=user.is_active,
        role_id=link.role_id,
        role_name=link.role.name,
    )


@router.get("/users", response_model=list[CompanyUserOut])
def list_users(
    current: CurrentUser = Depends(require_permission("utilizadores.utilizador.ver")),
    db: Session = Depends(get_db),
):
    rows = db.execute(
        select(User, UserCompanyRole)
        .join(UserCompanyRole, UserCompanyRole.user_id == User.id)
        .order_by(User.name)
    ).all()
    return [_company_user(u, link) for u, link in rows]


@router.post("/users", response_model=CompanyUserOut, status_code=status.HTTP_201_CREATED)
def invite_user(
    data: UserInvite,
    current: CurrentUser = Depends(require_permission("utilizadores.utilizador.gerir")),
    db: Session = Depends(get_db),
):
    role = service.get_role(db, data.role_id)
    user = service.create_user(
        db, tenant_id=current.tenant_id, name=data.name, email=data.email, password=data.password
    )
    link = service.assign_role(db, user=user, company_id=current.company_id, role=role)
    audit.record(
        db,
        tenant_id=current.tenant_id,
        company_id=current.company_id,
        user_id=current.id,
        action="create",
        entity="user",
        entity_id=user.id,
        after={"email": user.email, "role": role.name},
        ip=current.ip,
    )
    db.commit()
    return _company_user(user, link)


@router.put("/users/{user_id}/role", response_model=CompanyUserOut)
def change_role(
    user_id: uuid.UUID,
    data: UserRoleUpdate,
    current: CurrentUser = Depends(require_permission("utilizadores.utilizador.gerir")),
    db: Session = Depends(get_db),
):
    link = db.scalar(select(UserCompanyRole).where(UserCompanyRole.user_id == user_id))
    if link is None:
        raise NotFound("USER_NOT_FOUND", "Utilizador não encontrado nesta empresa.")
    role = service.get_role(db, data.role_id)
    before = {"role": link.role.name}
    link.role_id = role.id
    db.flush()
    db.refresh(link)
    audit.record(
        db,
        tenant_id=current.tenant_id,
        company_id=current.company_id,
        user_id=current.id,
        action="change_role",
        entity="user",
        entity_id=user_id,
        before=before,
        after={"role": role.name},
        ip=current.ip,
    )
    db.commit()
    return _company_user(db.get(User, user_id), link)


@router.get("/roles", response_model=list[RoleOut])
def list_roles(
    current: CurrentUser = Depends(require_permission("utilizadores.papel.ver")),
    db: Session = Depends(get_db),
):
    return db.scalars(select(Role).order_by(Role.name)).all()


@router.post("/roles", response_model=RoleOut, status_code=status.HTTP_201_CREATED)
def create_role(
    data: RoleCreate,
    current: CurrentUser = Depends(require_permission("utilizadores.papel.gerir")),
    db: Session = Depends(get_db),
):
    role = service.create_role(
        db,
        tenant_id=current.tenant_id,
        company_id=current.company_id,
        name=data.name,
        description=data.description,
        codes=data.permission_codes,
    )
    audit.record(
        db,
        tenant_id=current.tenant_id,
        company_id=current.company_id,
        user_id=current.id,
        action="create",
        entity="role",
        entity_id=role.id,
        after={"name": role.name, "permissions": role.permission_codes},
        ip=current.ip,
    )
    db.commit()
    return role


@router.get("/permissions", response_model=list[PermissionOut])
def list_permissions(
    current: CurrentUser = Depends(require_permission("utilizadores.papel.ver")),
):
    return [PermissionOut(code=c, description=d) for c, d in sorted(PERMISSIONS.items())]
