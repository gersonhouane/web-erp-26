import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import JSON, DateTime, ForeignKey, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.shared.models import Base, CompanyScoped, IdMixin, TenantScoped, TimestampMixin


class Tenant(IdMixin, TimestampMixin, Base):
    """Organização: o cliente do SaaS. Agrupa empresas e utilizadores."""

    __tablename__ = "tenant"

    name: Mapped[str] = mapped_column(String(200))
    status: Mapped[str] = mapped_column(String(20), default="trial")  # trial|active|suspended


class Company(IdMixin, TimestampMixin, TenantScoped, Base):
    """Entidade legal com NUIT, país, moeda e regras fiscais próprias."""

    __tablename__ = "company"
    __table_args__ = (UniqueConstraint("tenant_id", "nuit", name="uq_company_tenant_nuit"),)

    name: Mapped[str] = mapped_column(String(200))
    nuit: Mapped[str | None] = mapped_column(String(20))
    country_code: Mapped[str] = mapped_column(String(2), default="MZ")
    base_currency: Mapped[str] = mapped_column(String(3), default="MZN")
    address_street: Mapped[str | None] = mapped_column(String(200))
    address_neighbourhood: Mapped[str | None] = mapped_column(String(120))
    address_number: Mapped[str | None] = mapped_column(String(20))
    city: Mapped[str | None] = mapped_column(String(120))
    province: Mapped[str | None] = mapped_column(String(120))
    fiscal_area: Mapped[str | None] = mapped_column(String(200))
    is_active: Mapped[bool] = mapped_column(default=True)


class Branch(IdMixin, TimestampMixin, CompanyScoped, Base):
    """Filial, loja, armazém ou ponto de venda de uma empresa."""

    __tablename__ = "branch"

    name: Mapped[str] = mapped_column(String(200))
    address: Mapped[str | None] = mapped_column(String(300))
    is_active: Mapped[bool] = mapped_column(default=True)


class AuditLog(IdMixin, TenantScoped, Base):
    __tablename__ = "audit_log"

    company_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("company.id", ondelete="CASCADE"), index=True
    )
    user_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("app_user.id", ondelete="SET NULL")
    )
    action: Mapped[str] = mapped_column(String(60))
    entity: Mapped[str] = mapped_column(String(60))
    entity_id: Mapped[str | None] = mapped_column(String(64))
    before: Mapped[dict[str, Any] | None] = mapped_column(JSON)
    after: Mapped[dict[str, Any] | None] = mapped_column(JSON)
    ip: Mapped[str | None] = mapped_column(String(45))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), index=True
    )
