from sqlalchemy import select

from app.core.db import SessionLocal, set_rls_context
from app.modules.core.models import Branch, Company
from tests.conftest import auth, signup


def test_switch_between_companies_of_same_organization(client):
    tokens = signup(client)
    r = client.post(
        "/api/v1/core/companies",
        json={"name": "Exemplo Logística", "nuit": "400000002"},
        headers=auth(tokens),
    )
    assert r.status_code == 201
    second = r.json()["id"]

    client.post("/api/v1/core/branches", json={"name": "Loja Beira"}, headers=auth(tokens))
    switched = client.post(
        "/api/v1/auth/switch-company", json={"company_id": second}, headers=auth(tokens)
    ).json()
    assert switched["company_id"] == second
    # A filial da primeira empresa não aparece na segunda.
    assert client.get("/api/v1/core/branches", headers=auth(switched)).json() == []
    me = client.get("/api/v1/auth/me", headers=auth(switched)).json()
    assert len(me["companies"]) == 2


def test_cannot_switch_to_another_organizations_company(client):
    a = signup(client)
    b = signup(client, email="b@outra.co.mz", org="Outra", company="Outra Lda", nuit="400000009")
    r = client.post(
        "/api/v1/auth/switch-company", json={"company_id": b["company_id"]}, headers=auth(a)
    )
    assert r.status_code == 403 and r.json()["code"] == "COMPANY_ACCESS_DENIED"


def test_row_level_security_hides_other_companies_in_the_database(client):
    a = signup(client)
    b = signup(client, email="b@outra.co.mz", org="Outra", company="Outra Lda", nuit="400000009")
    client.post("/api/v1/core/branches", json={"name": "Filial A"}, headers=auth(a))
    client.post("/api/v1/core/branches", json={"name": "Filial B"}, headers=auth(b))

    with SessionLocal() as db:
        set_rls_context(db, company_id=a["company_id"])
        names = db.scalars(select(Branch.name)).all()
        assert names == ["Filial A"]
        # Sem contexto nenhum, a base de dados não devolve nada.
        set_rls_context(db)
        assert db.scalars(select(Branch.name)).all() == []
        assert db.scalars(select(Company.name)).all() == []
