import uuid
import pytest


def project_payload():
    return {
        "name": f"Test Highway Project {uuid.uuid4().hex[:6]}",
        "description": "Test project for automated tests",
        "project_type": "NATIONAL_HIGHWAY",
        "purpose": "Road construction and development",
        "public_category": "INFRASTRUCTURE",
        "priority": 3,
        "estimated_cost": 1500000000.00,
        "funding_source": "Central Government",
    }


@pytest.mark.anyio
async def test_create_project(client, admin_token):
    assert admin_token is not None
    headers = {"Authorization": f"Bearer {admin_token}"}
    response = await client.post(
        "/api/v1/projects",
        json=project_payload(),
        headers=headers,
    )
    assert response.status_code == 201
    data = response.json()["data"]
    assert data["project_code"].startswith("BD-")
    assert "id" in data
    assert data["status"] == "DRAFT"


@pytest.mark.anyio
async def test_create_project_unauthenticated(client):
    response = await client.post(
        "/api/v1/projects",
        json=project_payload(),
    )
    assert response.status_code == 401


@pytest.mark.anyio
async def test_list_projects(client, admin_token):
    assert admin_token is not None
    headers = {"Authorization": f"Bearer {admin_token}"}
    response = await client.get(
        "/api/v1/projects?page=1&page_size=5",
        headers=headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert "data" in data
    assert "total" in data


@pytest.mark.anyio
async def test_get_project(client, admin_token):
    assert admin_token is not None
    headers = {"Authorization": f"Bearer {admin_token}"}
    create_resp = await client.post(
        "/api/v1/projects",
        json=project_payload(),
        headers=headers,
    )
    project_id = create_resp.json()["data"]["id"]
    response = await client.get(f"/api/v1/projects/{project_id}", headers=headers)
    assert response.status_code == 200
    assert response.json()["data"]["id"] == project_id


@pytest.mark.anyio
async def test_get_project_not_found(client, admin_token):
    assert admin_token is not None
    headers = {"Authorization": f"Bearer {admin_token}"}
    fake_id = "00000000-0000-0000-0000-000000000000"
    response = await client.get(f"/api/v1/projects/{fake_id}", headers=headers)
    assert response.status_code == 404


@pytest.mark.anyio
async def test_update_project(client, admin_token):
    assert admin_token is not None
    headers = {"Authorization": f"Bearer {admin_token}"}
    create_resp = await client.post(
        "/api/v1/projects",
        json=project_payload(),
        headers=headers,
    )
    project_id = create_resp.json()["data"]["id"]
    response = await client.put(
        f"/api/v1/projects/{project_id}",
        json={"name": "Updated Project Name", "priority": 2},
        headers=headers,
    )
    assert response.status_code == 200
    assert response.json()["data"]["name"] == "Updated Project Name"
    assert response.json()["data"]["version"] == 2


@pytest.mark.anyio
async def test_submit_project(client, admin_token):
    assert admin_token is not None
    headers = {"Authorization": f"Bearer {admin_token}"}
    create_resp = await client.post(
        "/api/v1/projects",
        json=project_payload(),
        headers=headers,
    )
    project_id = create_resp.json()["data"]["id"]
    response = await client.post(
        f"/api/v1/projects/{project_id}/submit",
        json={"comment": "Ready for review"},
        headers=headers,
    )
    assert response.status_code == 200
    assert response.json()["data"]["status"] == "SUBMITTED"


@pytest.mark.anyio
async def test_project_filter_by_status(client, admin_token):
    assert admin_token is not None
    headers = {"Authorization": f"Bearer {admin_token}"}
    response = await client.get(
        "/api/v1/projects?status=DRAFT",
        headers=headers,
    )
    assert response.status_code == 200
    for item in response.json()["data"]:
        assert item["status"] == "DRAFT"


@pytest.mark.anyio
async def test_get_project_timeline(client, admin_token):
    assert admin_token is not None
    headers = {"Authorization": f"Bearer {admin_token}"}
    create_resp = await client.post(
        "/api/v1/projects",
        json=project_payload(),
        headers=headers,
    )
    project_id = create_resp.json()["data"]["id"]
    response = await client.get(f"/api/v1/projects/{project_id}/timeline", headers=headers)
    assert response.status_code == 200
    assert len(response.json()["data"]) >= 1


@pytest.mark.anyio
async def test_get_project_activity(client, admin_token):
    assert admin_token is not None
    headers = {"Authorization": f"Bearer {admin_token}"}
    create_resp = await client.post(
        "/api/v1/projects",
        json=project_payload(),
        headers=headers,
    )
    project_id = create_resp.json()["data"]["id"]
    response = await client.get(f"/api/v1/projects/{project_id}/activity", headers=headers)
    assert response.status_code == 200
    assert response.json()["total"] >= 1
