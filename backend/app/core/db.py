"""Ligação à base de dados e contexto de Row-Level Security.

Cada sessão guarda em `session.info` a organização e a empresa activas. Sempre que
uma transacção começa, esses valores são aplicados com `set_config(..., true)`, que
só dura até ao fim da transacção. As políticas RLS do PostgreSQL leem-nos.
"""

from collections.abc import Iterator
from contextlib import contextmanager
from uuid import UUID

from sqlalchemy import create_engine, event, text
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import get_settings

engine = create_engine(get_settings().database_url, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)

_RLS_KEYS = ("tenant_id", "company_id", "rls_bypass")


@event.listens_for(Session, "after_begin")
def _apply_rls_context(session: Session, transaction, connection) -> None:
    if not any(k in session.info for k in _RLS_KEYS):
        return
    connection.execute(
        text(
            "SELECT set_config('app.tenant_id', :t, true),"
            " set_config('app.company_id', :c, true),"
            " set_config('app.rls_bypass', :b, true)"
        ),
        {
            "t": str(session.info.get("tenant_id") or ""),
            "c": str(session.info.get("company_id") or ""),
            "b": "on" if session.info.get("rls_bypass") else "off",
        },
    )


def set_rls_context(
    session: Session,
    *,
    tenant_id: UUID | None = None,
    company_id: UUID | None = None,
    bypass: bool = False,
) -> None:
    """Define a organização e a empresa visíveis para esta sessão.

    `bypass=True` só deve ser usado em operações de sistema (registo, login).
    Se já houver uma transacção aberta, o contexto é aplicado de imediato.
    """
    session.info["tenant_id"] = tenant_id
    session.info["company_id"] = company_id
    session.info["rls_bypass"] = bypass
    if session.in_transaction():
        _apply_rls_context(session, None, session.connection())


@contextmanager
def rls_bypass(session: Session) -> Iterator[None]:
    """Modo de sistema temporário; repõe o contexto anterior no fim."""
    previous = {k: session.info.get(k) for k in _RLS_KEYS}
    set_rls_context(
        session, tenant_id=previous["tenant_id"], company_id=previous["company_id"], bypass=True
    )
    try:
        yield
    finally:
        set_rls_context(
            session,
            tenant_id=previous["tenant_id"],
            company_id=previous["company_id"],
            bypass=bool(previous["rls_bypass"]),
        )
