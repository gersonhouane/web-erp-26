from fastapi import APIRouter, Depends, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.db import rls_bypass
from app.core.deps import CurrentUser, get_current_user, get_db, require_permission
from app.core.errors import NotFound
from app.modules.auth.service import user_companies
from app.modules.core.models import AuditLog, Branch, Company
from app.modules.core.schemas import (
    AuditLogOut,
    BranchCreate,
    BranchOut,
    CompanyCreate,
    CompanyOut,
    CompanyUpdate,
)
from app.modules.core.service import create_company
from app.shared import audit
from app.shared.pagination import Page, PageParams, page_params, paginate

router = APIRouter(prefix="/core", tags=["core"])


@router.get("/companies/current", response_model=CompanyOut)
def current_company(
    current: CurrentUser = Depends(require_permission("core.empresa.ver")),
    db: Session = Depends(get_db),
):
    company = db.get(Company, current.company_id)
    if company is None:
        raise NotFound("COMPANY_NOT_FOUND", "Empresa não encontrada.")
    return company


@router.patch("/companies/current", response_model=CompanyOut)
def update_current_company(
    data: CompanyUpdate,
    current: CurrentUser = Depends(require_permission("core.empresa.gerir")),
    db: Session = Depends(get_db),
):
    company = db.get(Company, current.company_id)
    if company is None:
        raise NotFound("COMPANY_NOT_FOUND", "Empresa não encontrada.")
    changes = data.model_dump(exclude_unset=True)
    before = {k: getattr(company, k) for k in changes}
    for key, value in changes.items():
        setattr(company, key, value)
    audit.record(
        db,
        tenant_id=current.tenant_id,
        company_id=company.id,
        user_id=current.id,
        action="update",
        entity="company",
        entity_id=company.id,
        before=before,
        after=changes,
        ip=current.ip,
    )
    db.commit()
    return company


@router.post("/companies", response_model=CompanyOut, status_code=status.HTTP_201_CREATED)
def add_company(
    data: CompanyCreate,
    current: CurrentUser = Depends(require_permission("core.empresa.gerir")),
    db: Session = Depends(get_db),
):
    """Cria outra empresa na mesma organização. Quem a cria fica administrador dela."""
    with rls_bypass(db):
        company = create_company(db, tenant_id=current.tenant_id, data=data, owner=current.user)
        audit.record(
            db,
            tenant_id=current.tenant_id,
            company_id=company.id,
            user_id=current.id,
            action="create",
            entity="company",
            entity_id=company.id,
            after={"name": company.name, "nuit": company.nuit},
            ip=current.ip,
        )
        db.commit()
    return company


@router.get("/branches", response_model=list[BranchOut])
def list_branches(
    current: CurrentUser = Depends(require_permission("core.filial.ver")),
    db: Session = Depends(get_db),
):
    return db.scalars(select(Branch).order_by(Branch.name)).all()


@router.post("/branches", response_model=BranchOut, status_code=status.HTTP_201_CREATED)
def create_branch(
    data: BranchCreate,
    current: CurrentUser = Depends(require_permission("core.filial.gerir")),
    db: Session = Depends(get_db),
):
    branch = Branch(tenant_id=current.tenant_id, company_id=current.company_id, **data.model_dump())
    db.add(branch)
    db.flush()
    audit.record(
        db,
        tenant_id=current.tenant_id,
        company_id=current.company_id,
        user_id=current.id,
        action="create",
        entity="branch",
        entity_id=branch.id,
        after=data.model_dump(),
        ip=current.ip,
    )
    db.commit()
    return branch


@router.get("/audit-log", response_model=Page[AuditLogOut])
def audit_log(
    params: PageParams = Depends(page_params),
    current: CurrentUser = Depends(require_permission("core.auditoria.ver")),
    db: Session = Depends(get_db),
):
    stmt = select(AuditLog).order_by(AuditLog.created_at.desc())
    items, total = paginate(db, stmt, params)
    return Page(items=items, total=total, page=params.page, size=params.size)


@router.get("/companies", response_model=list[CompanyOut])
def my_companies(current: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)):
    """Empresas da organização a que o utilizador tem acesso."""
    return [company for company, _ in user_companies(db, current.user)]
