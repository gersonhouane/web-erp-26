"""Importa todos os modelos e permissões, para o Alembic e o SQLAlchemy os conhecerem."""

import app.modules.core.permissions  # noqa: F401
import app.modules.users.permissions  # noqa: F401
from app.modules.core.models import AuditLog, Branch, Company, Tenant  # noqa: F401
from app.modules.users.models import (  # noqa: F401
    RefreshToken,
    Role,
    RolePermission,
    User,
    UserCompanyRole,
)
from app.shared.models import Base  # noqa: F401
