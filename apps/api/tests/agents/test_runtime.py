import pytest
import uuid
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.agent import Agent as DBAgent
from app.core.security import create_access_token
from app.agents.runtime import agent_runtime
from tests.agents.test_sdk import seed_agent_test_data

@pytest.mark.asyncio
async def test_agent_runtime_registration_and_health(db_session: AsyncSession):
    await agent_runtime.initialize()
    
    # Check health check reports ok
    health = await agent_runtime.health_check()
    assert health["status"] == "healthy"
    assert health["details"]["registered_tools_count"] > 0
    assert health["details"]["registered_agents_count"] > 0

@pytest.mark.asyncio
async def test_agents_api_flow(client: AsyncClient, db_session: AsyncSession):
    # Seed user and org
    user, org = await seed_agent_test_data(db_session)
    token = create_access_token(subject=str(user.id))
    
    headers = {
        "Authorization": f"Bearer {token}",
        "X-Organization-ID": str(org.id)
    }

    # Initialize runtime
    await agent_runtime.initialize()

    # 1. GET /api/v1/agents
    response = await client.get("/api/v1/agents", headers=headers)
    assert response.status_code == 200
    agents_list = response.json()
    assert len(agents_list) > 0
    
    # Find ResearchAgent
    research_agent_meta = next((a for a in agents_list if a["name"] == "ResearchAgent"), None)
    assert research_agent_meta is not None
    assert research_agent_meta["version"] == "1.0.0"

    # 2. GET /api/v1/agents/{id}
    response = await client.get(f"/api/v1/agents/research", headers=headers)
    assert response.status_code == 200
    details = response.json()
    assert details["name"] == "ResearchAgent"

    # 3. GET /api/v1/tools
    response = await client.get("/api/v1/tools", headers=headers)
    assert response.status_code == 200
    tools_list = response.json()
    assert len(tools_list) > 0
    assert any(t["name"] == "search_documents" for t in tools_list)

    # 4. GET /api/v1/tools/{name}
    response = await client.get("/api/v1/tools/search_documents", headers=headers)
    assert response.status_code == 200
    tool_details = response.json()
    assert tool_details["name"] == "search_documents"
    assert "query" in tool_details["input_schema"]["properties"]

    # 5. POST /api/v1/agents/{id}/execute
    exec_payload = {
        "input": {
            "query": "sprint planning"
        }
    }
    response = await client.post("/api/v1/agents/research/execute", json=exec_payload, headers=headers)
    assert response.status_code == 200
    exec_result = response.json()
    assert exec_result["status"] == "success"
    assert exec_result["agent"]["name"] == "ResearchAgent"
    assert "synthesis" in exec_result["result"]

    # 6. GET /api/v1/agents/{id}/status
    response = await client.get("/api/v1/agents/research/status", headers=headers)
    assert response.status_code == 200
    status_details = response.json()
    assert status_details["executions"] == 1
    assert status_details["success_rate"] == 1.0
