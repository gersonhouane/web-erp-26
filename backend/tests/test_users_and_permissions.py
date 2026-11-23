from tests.conftest import auth, signup


def _role_id(client, tokens, name):
    roles = client.get("/api/v1/roles", headers=auth(tokens)).json()
    return next(r["id"] for r in roles if r["name"] == name)


def test_admin_invites_user_who_gets_only_role_permissions(client):
    admin = signup(client)
    r = client.post(
        "/api/v1/users",
        json={
            "name": "Vendedor Um",
            "email": "vendedor@exemplo.co.mz",
            "password": "senha-segura-2",
            "role_id": _role_id(client, admin, "Consulta"),
        },
        headers=auth(admin),
    )
    assert r.status_code == 201 and r.json()["role_name"] == "Consulta"

    seller = client.post(
        "/api/v1/auth/login",
        json={"email": "vendedor@exemplo.co.mz", "password": "senha-segura-2"},
    ).json()
    assert client.get("/api/v1/core/branches", headers=auth(seller)).status_code == 200
    r = client.post("/api/v1/core/branches", json={"name": "Nova"}, headers=auth(seller))
    assert r.status_code == 403 and r.json()["code"] == "PERMISSION_DENIED"


def test_custom_role_and_audit_log(client):
    admin = signup(client)
    r = client.post(
        "/api/v1/roles",
        json={"name": "Filiais", "permission_codes": ["core.filial.ver", "core.filial.gerir"]},
        headers=auth(admin),
    )
    assert r.status_code == 201
    assert r.json()["permission_codes"] == ["core.filial.gerir", "core.filial.ver"]

    r = client.post(
        "/api/v1/roles",
        json={"name": "Má", "permission_codes": ["nao.existe.x"]},
        headers=auth(admin),
    )
    assert r.json()["code"] == "PERMISSION_NOT_FOUND"

    log = client.get("/api/v1/core/audit-log", headers=auth(admin)).json()
    actions = [(i["action"], i["entity"]) for i in log["items"]]
    assert ("create", "role") in actions and ("signup", "tenant") in actions
