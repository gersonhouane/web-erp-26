import uuid

from sqlalchemy.orm import Session

from app.modules.core.models import Company
from app.modules.core.schemas import CompanyCreate
from app.modules.users.models import User
from app.modules.users.service import assign_role, create_system_roles


def create_company(
    db: Session, *, tenant_id: uuid.UUID, data: CompanyCreate, owner: User
) -> Company:
    """Cria a empresa, os papéis padrão, e torna `owner` administrador dela."""
    company = Company(tenant_id=tenant_id, **data.model_dump())
    db.add(company)
    db.flush()
    roles = create_system_roles(db, tenant_id=tenant_id, company_id=company.id)
    assign_role(db, user=owner, company_id=company.id, role=roles["Administrador"])
    return company
