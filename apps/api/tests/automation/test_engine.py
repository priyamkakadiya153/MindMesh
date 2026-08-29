import pytest
import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from app.automation.approval.models import WorkflowDefinition, WorkflowExecution, WorkflowStepExecution
from app.automation.workflow.engine import WorkflowEngine
from app.automation.workflow.orchestrator import WorkflowOrchestrator
from app.automation.workflow.validator import WorkflowValidator
from tests.agents.test_sdk import seed_agent_test_data

def test_workflow_validator():
    # Valid
    valid_def = {
        "trigger": {"type": "manual"},
        "steps": [
            {"name": "step_1", "type": "sequential"},
            {"name": "step_2", "type": "sequential", "dependencies": ["step_1"]}
        ]
    }
    assert len(WorkflowValidator.validate_definition(valid_def)) == 0

    # Cyclic
    cyclic_def = {
        "trigger": {"type": "manual"},
        "steps": [
            {"name": "step_1", "type": "sequential", "dependencies": ["step_2"]},
            {"name": "step_2", "type": "sequential", "dependencies": ["step_1"]}
        ]
    }
    assert "Cyclic dependency loop detected" in "".join(WorkflowValidator.validate_definition(cyclic_def))

@pytest.mark.asyncio
async def test_sequential_workflow_execution(db_session: AsyncSession):
    user, org = await seed_agent_test_data(db_session)
    
    # 1. Create a simple 2-step definition
    definition = {
        "trigger": {"type": "manual"},
        "steps": [
            {"name": "step_1", "type": "sequential"},
            {
                "name": "step_2",
                "type": "sequential",
                "dependencies": ["step_1"],
                "condition": "${step_1.result.message} == 'Step executed successfully.'"
            }
        ]
    }
    
    wdef = WorkflowDefinition(
        name="Sequential Test",
        definition=definition,
        organization_id=org.id
    )
    db_session.add(wdef)
    await db_session.commit()

    # 2. Trigger execution
    execution = await WorkflowOrchestrator.start_execution(
        db=db_session,
        workflow_id=wdef.id,
        initial_context={},
        organization_id=org.id
    )

    assert execution.status == "Completed"
    assert execution.current_step_index == 0
    
    # Check that both steps were executed
    from sqlalchemy import select
    stmt = select(WorkflowStepExecution).where(WorkflowStepExecution.execution_id == execution.id)
    res = await db_session.execute(stmt)
    logs = res.scalars().all()
    assert len(logs) == 2
    assert all(log.status == "Completed" for log in logs)

@pytest.mark.asyncio
async def test_workflow_rollback_on_failure(db_session: AsyncSession):
    user, org = await seed_agent_test_data(db_session)

    # step_1 (with compensation) -> step_2 (fails)
    definition = {
        "trigger": {"type": "manual"},
        "steps": [
            {
                "name": "step_1",
                "type": "sequential",
                "compensation_step": {"type": "delete_project"}
            },
            {
                "name": "step_2",
                "type": "ai_agent",
                "agent_name": "NonExistentAgent", # Fails loading
                "dependencies": ["step_1"]
            }
        ]
    }

    wdef = WorkflowDefinition(
        name="Rollback Test",
        definition=definition,
        organization_id=org.id
    )
    db_session.add(wdef)
    await db_session.commit()

    # Trigger execution (will fail and trigger rollback)
    execution = await WorkflowOrchestrator.start_execution(
        db=db_session,
        workflow_id=wdef.id,
        initial_context={"project_id": "test-project-123"},
        organization_id=org.id
    )

    # Workflow execution is rolled back
    assert execution.status == "Rolled Back"

    from sqlalchemy import select
    stmt = select(WorkflowStepExecution).where(WorkflowStepExecution.execution_id == execution.id)
    res = await db_session.execute(stmt)
    logs = res.scalars().all()
    
    # step_1 is rolled back, step_2 failed
    step_1_log = next(log for log in logs if log.step_name == "step_1")
    step_2_log = next(log for log in logs if log.step_name == "step_2")
    assert step_1_log.status == "Rolled Back"
    assert step_2_log.status == "Failed"
