from tests.conftest import auth, signup


def test_signup_creates_admin_with_all_permissions(client):
    tokens = signup(client)
    me = client.get("/api/v1/auth/me", headers=auth(tokens)).json()
    assert me["email"] == "admin@exemplo.co.mz"
    assert [c["role"] for c in me["companies"]] == ["Administrador"]
    assert "utilizadores.utilizador.gerir" in me["permissions"]
    assert "core.empresa.gerir" in me["permissions"]


def test_signup_rejects_duplicate_email_and_bad_nuit(client):
    signup(client)
    r = client.post(
        "/api/v1/auth/signup",
        json={
            "organization_name": "Outra",
            "company": {"name": "Outra Lda", "nuit": "123"},
            "name": "Outro Admin",
            "email": "novo@exemplo.co.mz",
            "password": "senha-segura-1",
        },
    )
    assert r.status_code == 422 and r.json()["code"] == "VALIDATION_ERROR"
    r = client.post(
        "/api/v1/auth/signup",
        json={
            "organization_name": "Outra",
            "company": {"name": "Outra Lda"},
            "name": "Outro Admin",
            "email": "ADMIN@exemplo.co.mz",
            "password": "senha-segura-1",
        },
    )
    assert r.status_code == 409 and r.json()["code"] == "EMAIL_IN_USE"


def test_login_locks_after_five_failures(client):
    signup(client)
    for _ in range(5):
        r = client.post(
            "/api/v1/auth/login", json={"email": "admin@exemplo.co.mz", "password": "errada"}
        )
        assert r.json()["code"] == "INVALID_CREDENTIALS"
    r = client.post(
        "/api/v1/auth/login", json={"email": "admin@exemplo.co.mz", "password": "senha-segura-1"}
    )
    assert r.status_code == 401 and r.json()["code"] == "ACCOUNT_LOCKED"


def test_refresh_rotates_and_detects_reuse(client):
    tokens = signup(client)
    r = client.post("/api/v1/auth/refresh", json={"refresh_token": tokens["refresh_token"]})
    assert r.status_code == 200
    new = r.json()
    assert new["refresh_token"] != tokens["refresh_token"]
    # Reutilizar o token antigo revoga também o novo.
    r = client.post("/api/v1/auth/refresh", json={"refresh_token": tokens["refresh_token"]})
    assert r.status_code == 401
    r = client.post("/api/v1/auth/refresh", json={"refresh_token": new["refresh_token"]})
    assert r.status_code == 401


def test_logout_revokes_refresh_token(client):
    tokens = signup(client)
    assert (
        client.post(
            "/api/v1/auth/logout", json={"refresh_token": tokens["refresh_token"]}
        ).status_code
        == 204
    )
    r = client.post("/api/v1/auth/refresh", json={"refresh_token": tokens["refresh_token"]})
    assert r.status_code == 401


def test_requests_without_token_are_rejected(client):
    r = client.get("/api/v1/auth/me")
    assert r.status_code == 401 and r.json()["code"] == "NOT_AUTHENTICATED"
    r = client.get("/api/v1/auth/me", headers={"Authorization": "Bearer lixo"})
    assert r.json()["code"] == "INVALID_TOKEN"
