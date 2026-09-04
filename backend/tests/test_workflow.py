import uuid
import pytest


@pytest.mark.anyio
async def test_valid_transition_draft_to_submitted(client, admin_token):
    if not admin_token:
        pytest.skip("No admin token")
    headers = {"Authorization": f"Bearer {admin_token}"}

    create_resp = await client.post(
        "/api/v1/projects",
        json={
            "name": f"Workflow Test Project {uuid.uuid4().hex[:6]}",
            "description": "Workflow transition test",
            "project_type": "RAILWAY",
            "priority": 2,
        },
        headers=headers,
    )
    project_id = create_resp.json()["data"]["id"]

    response = await client.post(
        f"/api/v1/workflow/project/{project_id}/transition",
        json={"new_status": "SUBMITTED", "comment": "Submitting for review"},
        headers=headers,
    )
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["to_status"] == "SUBMITTED"


@pytest.mark.anyio
async def test_illegal_transition_rejected(client, admin_token):
    if not admin_token:
        pytest.skip("No admin token")
    headers = {"Authorization": f"Bearer {admin_token}"}

    create_resp = await client.post(
        "/api/v1/projects",
        json={
            "name": f"Illegal Test Project {uuid.uuid4().hex[:6]}",
            "description": "Illegal transition test",
            "project_type": "DAM",
            "priority": 4,
        },
        headers=headers,
    )
    project_id = create_resp.json()["data"]["id"]

    response = await client.post(
        f"/api/v1/workflow/project/{project_id}/transition",
        json={"new_status": "APPROVED", "comment": "Should fail"},
        headers=headers,
    )
    assert response.status_code == 400


@pytest.mark.anyio
async def test_transition_same_status_rejected(client, admin_token):
    if not admin_token:
        pytest.skip("No admin token")
    headers = {"Authorization": f"Bearer {admin_token}"}

    create_resp = await client.post(
        "/api/v1/projects",
        json={
            "name": f"Same Status Project {uuid.uuid4().hex[:6]}",
            "description": "Same status transition test",
            "project_type": "MINING",
            "priority": 3,
        },
        headers=headers,
    )
    project_id = create_resp.json()["data"]["id"]

    response = await client.post(
        f"/api/v1/workflow/project/{project_id}/transition",
        json={"new_status": "DRAFT", "comment": "Same status"},
        headers=headers,
    )
    assert response.status_code == 400


@pytest.mark.anyio
async def test_multistep_workflow(client, admin_token):
    if not admin_token:
        pytest.skip("No admin token")
    headers = {"Authorization": f"Bearer {admin_token}"}

    create_resp = await client.post(
        "/api/v1/projects",
        json={
            "name": f"Multi Step Project {uuid.uuid4().hex[:6]}",
            "description": "Multi-step workflow test",
            "project_type": "POWER_PROJECT",
            "priority": 1,
        },
        headers=headers,
    )
    project_id = create_resp.json()["data"]["id"]

    steps = ["SUBMITTED", "UNDER_REVIEW", "JURISDICTION_CHECK",
             "GIS_VERIFICATION", "PUBLIC_HEARING", "COMPENSATION_ASSESSMENT",
             "RR_PLANNING", "APPROVED"]
    for step in steps:
        response = await client.post(
            f"/api/v1/workflow/project/{project_id}/transition",
            json={"new_status": step, "comment": f"Transition to {step}"},
            headers=headers,
        )
        assert response.status_code == 200, f"Failed at step {step}: {response.text}"


@pytest.mark.anyio
async def test_get_workflow_state(client, admin_token):
    if not admin_token:
        pytest.skip("No admin token")
    headers = {"Authorization": f"Bearer {admin_token}"}

    create_resp = await client.post(
        "/api/v1/projects",
        json={
            "name": f"State Test Project {uuid.uuid4().hex[:6]}",
            "description": "Workflow state test",
            "project_type": "URBAN_DEVELOPMENT",
            "priority": 3,
        },
        headers=headers,
    )
    project_id = create_resp.json()["data"]["id"]

    response = await client.get(
        f"/api/v1/workflow/project/{project_id}",
        headers=headers,
    )
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["current_status"] == "DRAFT"
    assert "SUBMITTED" in data["allowed_transitions"]


@pytest.mark.anyio
async def test_get_workflow_tasks(client, admin_token):
    if not admin_token:
        pytest.skip("No admin token")
    headers = {"Authorization": f"Bearer {admin_token}"}

    create_resp = await client.post(
        "/api/v1/projects",
        json={
            "name": f"Tasks Test Project {uuid.uuid4().hex[:6]}",
            "description": "Workflow tasks test",
            "project_type": "DEFENCE",
            "priority": 1,
        },
        headers=headers,
    )
    project_id = create_resp.json()["data"]["id"]

    await client.post(
        f"/api/v1/workflow/project/{project_id}/transition",
        json={"new_status": "SUBMITTED"},
        headers=headers,
    )

    response = await client.get(
        f"/api/v1/workflow/project/{project_id}/tasks",
        headers=headers,
    )
    assert response.status_code == 200
    assert len(response.json()["data"]) >= 1
