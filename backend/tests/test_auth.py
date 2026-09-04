import uuid
import pytest


@pytest.mark.anyio
async def test_register_user(client):
    email = f"newuser{uuid.uuid4().hex[:8]}@test.com"
    response = await client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": "Test@12345",
            "full_name": "Test User",
            "role_id": "a0000000-0000-0000-0000-000000000013",
        },
    )
    assert response.status_code == 201


@pytest.mark.anyio
async def test_register_duplicate_email(client):
    response = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "superadmin@bhudrishti.gov.in",
            "password": "Test@12345",
            "full_name": "Duplicate User",
            "role_id": "a0000000-0000-0000-0000-000000000013",
        },
    )
    assert response.status_code == 409


@pytest.mark.anyio
async def test_login_success(client):
    response = await client.post(
        "/api/v1/auth/login",
        json={"email": "superadmin@bhudrishti.gov.in", "password": "Super@123"},
    )
    assert response.status_code == 200
    data = response.json()["data"]
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"


@pytest.mark.anyio
async def test_login_failure(client):
    response = await client.post(
        "/api/v1/auth/login",
        json={"email": "superadmin@bhudrishti.gov.in", "password": "wrong-password"},
    )
    assert response.status_code == 401


@pytest.mark.anyio
async def test_login_validation_error(client):
    response = await client.post(
        "/api/v1/auth/login",
        json={"email": "not-an-email", "password": "123"},
    )
    assert response.status_code == 422


@pytest.mark.anyio
async def test_get_me(client, admin_token):
    assert admin_token is not None
    headers = {"Authorization": f"Bearer {admin_token}"}
    response = await client.get("/api/v1/auth/me", headers=headers)
    assert response.status_code == 200
    data = response.json()["data"]
    assert "email" in data
    assert "role" in data


@pytest.mark.anyio
async def test_get_me_unauthenticated(client):
    response = await client.get("/api/v1/auth/me")
    assert response.status_code == 401


@pytest.mark.anyio
async def test_refresh_token(client):
    response = await client.post(
        "/api/v1/auth/login",
        json={"email": "superadmin@bhudrishti.gov.in", "password": "Super@123"},
    )
    assert response.status_code == 200
    refresh_token = response.json()["data"]["refresh_token"]
    response = await client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": refresh_token},
    )
    assert response.status_code == 200
    assert "access_token" in response.json()["data"]
