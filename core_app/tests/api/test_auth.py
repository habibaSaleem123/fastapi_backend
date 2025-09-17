from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_signup_login_me_flow():
    # signup
    r = client.post("/auth/signup", json={"email":"alice@example.com","password":"pass1234","full_name":"Alice"})
    assert r.status_code in (201, 409)  # allow reruns

    # login
    r = client.post("/auth/login", json={"email":"alice@example.com","password":"pass1234"})
    assert r.status_code == 200, r.text
    access = r.json()["access_token"]
    assert "refresh_token" in r.headers.get("set-cookie", "").lower()

    # me
    r = client.get("/users/me", headers={"Authorization": f"Bearer {access}"})
    assert r.status_code == 200
    assert "id" in r.json()

    # refresh
    r = client.post("/auth/refresh")
    assert r.status_code == 200
    new_access = r.json()["access_token"]
    assert new_access and new_access != access

    # logout
    r = client.post("/auth/logout")
    assert r.status_code == 204
