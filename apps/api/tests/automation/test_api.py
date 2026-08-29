import pytest
import uuid
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.security import create_access_token
from tests.agents.test_sdk import seed_agent_test_data

@pytest.mark.asyncio
async def test_automation_http_apis(client: AsyncClient, db_session: AsyncSession):
    from datetime import datetime, timedelta
    from app.models.session import UserSession
    user, org = await seed_agent_test_data(db_session)

    sess = UserSession(
        id=uuid.uuid4(),
        user_id=user.id,
        refresh_token_hash=f"session_hash_{uuid.uuid4().hex}",
        expires_at=datetime.utcnow() + timedelta(days=1)
    )
    db_session.add(sess)
    await db_session.commit()

    token = create_access_token(subject=str(user.id), session_id=str(sess.id))
    
    headers = {
        "Authorization": f"Bearer {token}",
        "X-Organization-ID": str(org.id)
    }

    # 1. POST /api/v1/workflows (Create Definition)
    wf_payload = {
        "name": "Validation Pipeline",
        "description": "SLA approval validation flow",
        "definition": {
            "trigger": {"type": "manual"},
            "steps": [
                {
                    "name": "approval_step",
                    "type": "human_approval",
                    "title": "Document Approval Check",
                    "assigned_approver": str(user.id),
                    "policy_type": "Single"
                }
            ]
        },
        "organization_id": str(org.id)
    }

    response = await client.post("/api/v1/workflows", json=wf_payload, headers=headers)
    assert response.status_code == 201
    wdef = response.json()
    assert "id" in wdef
    workflow_id = wdef["id"]

    # 2. GET /api/v1/workflows (List Definitions)
    response = await client.get("/api/v1/workflows", headers=headers)
    assert response.status_code == 200
    assert len(response.json()) > 0

    # 3. GET /api/v1/workflows/{id} (Get Details)
    response = await client.get(f"/api/v1/workflows/{workflow_id}", headers=headers)
    assert response.status_code == 200
    assert response.json()["name"] == "Validation Pipeline"

    # 4. POST /api/v1/workflows/{id}/execute (Start Execution)
    exec_payload = {"test_run": True}
    response = await client.post(f"/api/v1/workflows/{workflow_id}/execute", json=exec_payload, headers=headers)
    assert response.status_code == 200
    execution = response.json()
    assert execution["status"] == "Waiting"
    execution_id = execution["id"]

    # 5. GET /api/v1/approvals (List approvals)
    response = await client.get("/api/v1/approvals", headers=headers)
    assert response.status_code == 200
    approvals = response.json()
    assert len(approvals) > 0
    
    # Locate approval linked to execution
    approval_id = next(a["id"] for a in approvals if a["workflow_execution_id"] == execution_id)

    # 6. POST /api/v1/approvals/{id}/approve (Approve HITL)
    approval_payload = {"vote": "Approved", "comments": "SLA check verified."}
    response = await client.post(f"/api/v1/approvals/{approval_id}/approve", json=approval_payload, headers=headers)
    assert response.status_code == 200
    assert response.json()["status"] == "Approved"

    # 7. POST /api/v1/events (Publish Event Log)
    event_payload = {
        "event_type": "document_uploaded",
        "payload": {"document_id": "doc-uuid-999"},
        "organization_id": str(org.id)
    }
    response = await client.post("/api/v1/events", json=event_payload, headers=headers)
    assert response.status_code == 201
    assert response.json()["event_type"] == "document_uploaded"

    # 8. GET /api/v1/events (List events log)
    response = await client.get("/api/v1/events", headers=headers)
    assert response.status_code == 200
    assert len(response.json()) > 0

    # 9. GET /api/v1/automation/dashboard (Dashboard KPIs telemetry)
    response = await client.get("/api/v1/automation/dashboard", headers=headers)
    assert response.status_code == 200
    kpis = response.json()
    assert "active_workflows" in kpis
    assert "pending_approvals" in kpis
    assert kpis["completed_workflows"] == 1
