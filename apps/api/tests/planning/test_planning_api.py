import pytest
import uuid
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.security import create_access_token
from app.agents.runtime import agent_runtime
from tests.agents.test_sdk import seed_agent_test_data
from app.workspace.models import Workspace, WorkspaceMember

async def seed_workspace_test_data(db: AsyncSession):
    user, org = await seed_agent_test_data(db)
    ws = Workspace(
        organization_id=org.id,
        name="Planning Workspace",
        slug="planning-workspace",
        is_default=True
    )
    db.add(ws)
    await db.flush()

    wsm = WorkspaceMember(
        workspace_id=ws.id,
        user_id=user.id,
        role="MEMBER"
    )
    db.add(wsm)
    await db.commit()
    return user, org, ws

@pytest.mark.asyncio
async def test_planning_and_execution_endpoints(client: AsyncClient, db_session: AsyncSession):
    # Seed user, org, workspace and initialize runtime
    user, org, ws = await seed_workspace_test_data(db_session)
    token = create_access_token(subject=str(user.id))
    
    headers = {
        "Authorization": f"Bearer {token}",
        "X-Organization-ID": str(org.id)
    }
    await agent_runtime.initialize()

    # 1. POST /api/v1/agents/plan
    plan_payload = {
        "goal": "Create project 'Automated Sprint' and create task 'QA validations'",
        "use_llm": False
    }
    response = await client.post("/api/v1/agents/plan", json=plan_payload, headers=headers)
    assert response.status_code == 200
    plan_data = response.json()
    assert "plan_id" in plan_data
    assert plan_data["feasibility"]["level"] == "HIGH"

    # 2. GET /api/v1/agents/plan/{id}
    plan_id = plan_data["plan_id"]
    response = await client.get(f"/api/v1/agents/plan/{plan_id}", headers=headers)
    assert response.status_code == 200
    assert response.json()["goal"] == plan_payload["goal"]

    # 3. POST /api/v1/agents/execute
    exec_payload = {
        "goal": "Create project 'Automated Execution' and create task 'CI checks'",
        "use_llm": False,
        "workspace_id": str(ws.id)
    }
    response = await client.post("/api/v1/agents/execute", json=exec_payload, headers=headers)
    assert response.status_code == 200
    exec_data = response.json()
    assert "execution_id" in exec_data
    assert exec_data["evaluation"]["success"] is True

    # 4. GET /api/v1/agents/executions/{id}
    execution_id = exec_data["execution_id"]
    response = await client.get(f"/api/v1/agents/executions/{execution_id}", headers=headers)
    assert response.status_code == 200
    assert response.json()["goal"] == exec_payload["goal"]

    # 5. POST /api/v1/tools/execute
    tool_payload = {
        "name": "create_task",
        "input": {
            "description": "Directly triggered tool task"
        }
    }
    response = await client.post("/api/v1/tools/execute", json=tool_payload, headers=headers)
    assert response.status_code == 200
    tool_data = response.json()
    assert tool_data["tool"] == "create_task"
    assert tool_data["reflection"]["success"] is True

    # 6. GET /api/v1/tools/discover
    response = await client.get("/api/v1/tools/discover", headers=headers)
    assert response.status_code == 200
    tools_list = response.json()
    assert len(tools_list) > 0

    # 7. POST /api/v1/agents/reflect
    reflect_payload = {
        "tool": "create_project",
        "result": {
            "id": "proj-123",
            "name": "Automated"
        }
    }
    response = await client.post("/api/v1/agents/reflect", json=reflect_payload, headers=headers)
    assert response.status_code == 200
    reflect_data = response.json()
    assert reflect_data["success"] is True
