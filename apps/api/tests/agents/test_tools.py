import pytest
from uuid import uuid4, UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.task import Task
from app.agents.context import SessionContext
from app.agents.tools.registry import tool_registry, register_built_in_tools
from app.agents.tools.resolver import ToolResolver
from app.agents.tools.executor import ToolExecutor
from app.agents.exceptions import PermissionDeniedException, ToolException
from tests.agents.test_sdk import seed_agent_test_data

@pytest.mark.asyncio
async def test_tool_registration():
    register_built_in_tools()
    
    # Verify built-in tools are registered
    assert tool_registry.get_tool("search_documents") is not None
    assert tool_registry.get_tool("create_task") is not None
    assert tool_registry.get_tool("send_notification") is not None
    assert tool_registry.get_tool("create_project") is not None

    meta = tool_registry.get_metadata("create_task")
    assert "description" in meta.input_schema["properties"]

@pytest.mark.asyncio
async def test_tool_permission_denied(db_session: AsyncSession):
    register_built_in_tools()
    user, org = await seed_agent_test_data(db_session)
    
    context = SessionContext(
        user_id=user.id,
        organization_id=org.id,
        permissions=["some_other_perm"], # missing tasks.write
        request_id=str(uuid4())
    )
    
    # Try calling create_task which requires tasks.write
    with pytest.raises(PermissionDeniedException):
        await ToolExecutor.execute(
            tool_name="create_task",
            input_data={"description": "Test Permission Denied"},
            context=context,
            db=db_session
        )

@pytest.mark.asyncio
async def test_tool_input_validation(db_session: AsyncSession):
    register_built_in_tools()
    user, org = await seed_agent_test_data(db_session)
    
    context = SessionContext(
        user_id=user.id,
        organization_id=org.id,
        permissions=["*"], # wildcard bypasses permission
        request_id=str(uuid4())
    )
    
    # 1. Missing description
    with pytest.raises(ToolException) as exc_info:
        await ToolExecutor.execute(
            tool_name="create_task",
            input_data={"project_id": str(uuid4())},
            context=context,
            db=db_session
        )
    assert "Missing required parameter" in str(exc_info.value)
    
    # 2. Wrong type for description
    with pytest.raises(ToolException) as exc_info:
        await ToolExecutor.execute(
            tool_name="create_task",
            input_data={"description": 12345},
            context=context,
            db=db_session
        )
    assert "must be a string" in str(exc_info.value)

@pytest.mark.asyncio
async def test_built_in_task_tool_execution(db_session: AsyncSession):
    register_built_in_tools()
    user, org = await seed_agent_test_data(db_session)
    
    context = SessionContext(
        user_id=user.id,
        organization_id=org.id,
        permissions=["*"],
        request_id=str(uuid4())
    )
    
    result = await ToolExecutor.execute(
        tool_name="create_task",
        input_data={"description": "Write integration test for agents"},
        context=context,
        db=db_session
    )
    
    assert result["id"] is not None
    assert result["description"] == "Write integration test for agents"
    assert result["status"] == "PENDING"

    # Query DB to make sure it was inserted
    stmt = select(Task).where(Task.id == UUID(result["id"]))
    res = await db_session.execute(stmt)
    db_task = res.scalar_one()
    assert db_task.description == "Write integration test for agents"
