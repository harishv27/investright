from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_profile_sync_and_patch():
    # 1. Signup / login user
    email = "profilesynctest@example.com"
    pwd = "password123"
    client.post("/api/auth/signup", json={"email": email, "password": pwd, "full_name": "Sync Test", "age": 28})
    login_res = client.post("/api/auth/login", json={"email": email, "password": pwd})
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Patch profile directly
    patch_res = client.patch("/api/profile", json={"income": 11600.0, "expenses": 2100.0}, headers=headers)
    assert patch_res.status_code == 200
    p = patch_res.json()
    assert p["income"] == 11600.0
    assert p["expenses"] == 2100.0

    # 3. Verify getProfile returns the updated values
    get_res = client.get("/api/profile", headers=headers)
    assert get_res.status_code == 200
    p2 = get_res.json()
    assert p2["income"] == 11600.0
    assert p2["expenses"] == 2100.0
