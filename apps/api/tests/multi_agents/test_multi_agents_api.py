import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.security import create_access_token
from app.agents.runtime import agent_runtime
from tests.agents.test_sdk import seed_agent_test_data

@pytest.mark.asyncio
async def test_multi_agent_api_endpoints(client: AsyncClient, db_session: AsyncSession):
    user, org = await seed_agent_test_data(db_session)
    token = create_access_token(subject=str(user.id))
    
    headers = {
        "Authorization": f"Bearer {token}",
        "X-Organization-ID": str(org.id)
    }
    await agent_runtime.initialize()

    # 1. POST /api/v1/orchestrator/execute
    exec_payload = {
        "goal": "Generate quarterly validation reports and verify compliance status",
        "use_llm": False
    }
    response = await client.post("/api/v1/orchestrator/execute", json=exec_payload, headers=headers)
    assert response.status_code == 200
    exec_data = response.json()
    assert "execution_id" in exec_data
    assert exec_data["status"] == "COMPLETED"

    # 2. GET /api/v1/orchestrator/{executionId}
    execution_id = exec_data["execution_id"]
    response = await client.get(f"/api/v1/orchestrator/{execution_id}", headers=headers)
    assert response.status_code == 200
    assert response.json()["goal"] == exec_payload["goal"]

    # 3. POST /api/v1/agents/delegate
    delegate_payload = {"description": "verify regulatory ISO policy compliance"}
    response = await client.post("/api/v1/agents/delegate", json=delegate_payload, headers=headers)
    assert response.status_code == 200
    delegate_data = response.json()
    assert delegate_data["assigned_agent"] == "ComplianceAgent"

    # 4. POST /api/v1/agents/message
    message_payload = {
        "sender": "PlannerAgent",
        "receiver": "ResearchAgent",
        "conversation_id": "test-chat-uuid",
        "payload": {"prompt": "Perform RAG index query"}
    }
    response = await client.post("/api/v1/agents/message", json=message_payload, headers=headers)
    assert response.status_code == 200
    assert response.json()["status"] == "SENT"

    # 5. GET /api/v1/executions
    response = await client.get("/api/v1/executions", headers=headers)
    assert response.status_code == 200
    executions_list = response.json()
    assert len(executions_list) > 0

    # 6. GET /api/v1/executions/{id}
    response = await client.get(f"/api/v1/executions/{execution_id}", headers=headers)
    assert response.status_code == 200
    assert response.json()["execution_id"] == execution_id
