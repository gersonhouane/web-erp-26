import uuid
from typing import Any

from sqlalchemy.orm import Session

from app.modules.core.models import AuditLog


def record(
    db: Session,
    *,
    tenant_id: uuid.UUID,
    company_id: uuid.UUID | None,
    user_id: uuid.UUID | None,
    action: str,
    entity: str,
    entity_id: uuid.UUID | str | None,
    before: dict[str, Any] | None = None,
    after: dict[str, Any] | None = None,
    ip: str | None = None,
) -> None:
    """Regista uma acção na auditoria, na mesma transacção da alteração."""
    db.add(
        AuditLog(
            tenant_id=tenant_id,
            company_id=company_id,
            user_id=user_id,
            action=action,
            entity=entity,
            entity_id=str(entity_id) if entity_id else None,
            before=before,
            after=after,
            ip=ip,
        )
    )
