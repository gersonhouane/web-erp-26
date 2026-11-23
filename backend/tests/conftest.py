import os

os.environ.setdefault(
    "WEBERP_DATABASE_URL", "postgresql+psycopg://weberp:weberp@localhost:5432/weberp_test"
)

import pytest  # noqa: E402
from alembic import command  # noqa: E402
from alembic.config import Config  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import text  # noqa: E402

from app.core.db import engine  # noqa: E402
from app.main import app  # noqa: E402

TABLES = (
    "audit_log, refresh_token, user_company_role, role_permission, role, branch,"
    " app_user, company, tenant"
)


@pytest.fixture(scope="session", autouse=True)
def _schema():
    cfg = Config(os.path.join(os.path.dirname(__file__), "..", "alembic.ini"))
    cfg.set_main_option(
        "script_location", os.path.join(os.path.dirname(__file__), "..", "migrations")
    )
    cfg.set_main_option("sqlalchemy.url", os.environ["WEBERP_DATABASE_URL"])
    command.downgrade(cfg, "base")
    command.upgrade(cfg, "head")
    yield


@pytest.fixture(autouse=True)
def _clean():
    yield
    with engine.begin() as conn:
        conn.execute(text(f"TRUNCATE {TABLES} CASCADE"))


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


def signup(
    client: TestClient,
    email: str = "admin@exemplo.co.mz",
    org: str = "Grupo Exemplo",
    company: str = "Exemplo Comercial",
    nuit: str = "400000001",
) -> dict:
    r = client.post(
        "/api/v1/auth/signup",
        json={
            "organization_name": org,
            "company": {"name": company, "nuit": nuit, "city": "Beira", "province": "Sofala"},
            "name": "Administrador",
            "email": email,
            "password": "senha-segura-1",
        },
    )
    assert r.status_code == 201, r.text
    return r.json()


def auth(tokens: dict) -> dict:
    return {"Authorization": f"Bearer {tokens['access_token']}"}
