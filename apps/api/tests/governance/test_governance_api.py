import pytest
import uuid
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.security import create_access_token
from app.governance.auditing import ActionAuditor
from tests.agents.test_sdk import seed_agent_test_data

@pytest.mark.asyncio
async def test_memory_and_governance_http_endpoints(client: AsyncClient, db_session: AsyncSession):
    user, org = await seed_agent_test_data(db_session)
    token = create_access_token(subject=str(user.id))
    
    headers = {
        "Authorization": f"Bearer {token}",
        "X-Organization-ID": str(org.id)
    }

    # 1. POST /api/v1/memory (Add Memory)
    project_uuid = str(uuid.uuid4())
    mem_payload = {
        "memory_type": "Project",
        "scope_key": project_uuid,
        "key": "milestone",
        "value": {"title": "Architecture approved"},
        "importance_score": 0.8
    }
    response = await client.post("/api/v1/memory", json=mem_payload, headers=headers)
    assert response.status_code == 201
    mem = response.json()
    assert "id" in mem
    memory_id = mem["id"]

    # 2. GET /api/v1/memory (List memories)
    response = await client.get("/api/v1/memory", headers=headers)
    assert response.status_code == 200
    assert len(response.json()) > 0

    # 3. POST /api/v1/memory/search (Search memories hierarchically)
    search_payload = {
        "query_key": "milestone",
        "project_id": project_uuid
    }
    response = await client.post("/api/v1/memory/search", json=search_payload, headers=headers)
    assert response.status_code == 200
    assert len(response.json()) > 0

    # 4. POST /api/v1/learning/feedback (Submit learning ratings)
    feedback_payload = {
        "rating": 5,
        "comment": "Perfect answer",
        "context_data": {"style": "concise"}
    }
    response = await client.post("/api/v1/learning/feedback", json=feedback_payload, headers=headers)
    assert response.status_code == 201
    assert response.json()["rating"] == 5

    # 5. GET /api/v1/learning/statistics (Fetch continuous learning telemetry)
    response = await client.get("/api/v1/learning/statistics", headers=headers)
    assert response.status_code == 200
    assert "average_feedback_rating" in response.json()

    # 6. POST /api/v1/governance/policies (Create governance policies)
    policy_payload = {
        "name": "PII Shield Rule",
        "category": "Privacy",
        "rules": {"pii_protection": True}
    }
    response = await client.post("/api/v1/governance/policies", json=policy_payload, headers=headers)
    assert response.status_code == 201
    policy = response.json()
    assert policy["category"] == "Privacy"

    # 7. GET /api/v1/governance/policies (List policies)
    response = await client.get("/api/v1/governance/policies", headers=headers)
    assert response.status_code == 200
    assert len(response.json()) > 0

    # 8. POST /api/v1/governance/validate (Dry-run validation checks)
    validate_payload = {
        "category": "Privacy",
        "context_data": {"text": "Contact me at admin@domain.com"}
    }
    response = await client.post("/api/v1/governance/validate", json=validate_payload, headers=headers)
    assert response.status_code == 200
    res_val = response.json()
    assert res_val["is_allowed"] is False
    assert len(res_val["violations"]) > 0

    # Create an audit decision log record for test
    run_uuid = uuid.uuid4()
    await ActionAuditor.log_action_decision(
        db=db_session,
        execution_id=run_uuid,
        organization_id=org.id,
        agent_name="SupervisorAgent",
        selected_tools=[],
        retrieved_documents=[],
        applied_policies=[],
        confidence_score=0.9,
        risk_score=0.1,
        trust_score=0.95
    )
    await db_session.commit()

    # 9. GET /api/v1/governance/trust/{executionId}
    response = await client.get(f"/api/v1/governance/trust/{run_uuid}", headers=headers)
    assert response.status_code == 200
    assert response.json()["trust_score"] == 0.95

    # 10. GET /api/v1/governance/explain/{executionId}
    response = await client.get(f"/api/v1/governance/explain/{run_uuid}", headers=headers)
    assert response.status_code == 200
    assert response.json()["agent_name"] == "SupervisorAgent"

    # 11. DELETE /api/v1/memory/{id} (Forget/delete memory)
    response = await client.delete(f"/api/v1/memory/{memory_id}", headers=headers)
    assert response.status_code == 200
