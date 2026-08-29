import pytest
import uuid
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.automation.approval.models import WorkflowDefinition, WorkflowExecution, ApprovalRequest
from app.automation.approval.service import ApprovalService
from app.automation.approval.escalation import ApprovalEscalator
from app.automation.approval.delegation import ApprovalDelegator
from app.automation.workflow.orchestrator import WorkflowOrchestrator
from tests.agents.test_sdk import seed_agent_test_data

@pytest.mark.asyncio
async def test_human_approval_resume_flow(db_session: AsyncSession):
    user, org = await seed_agent_test_data(db_session)

    # Simple workflow requiring human approval
    definition = {
        "trigger": {"type": "manual"},
        "steps": [
            {
                "name": "step_approval",
                "type": "human_approval",
                "assigned_approver": str(user.id),
                "title": "Manager Sign-off"
            },
            {
                "name": "step_after",
                "type": "sequential",
                "dependencies": ["step_approval"]
            }
        ]
    }

    wdef = WorkflowDefinition(
        name="Approval Flow Test",
        definition=definition,
        organization_id=org.id
    )
    db_session.add(wdef)
    await db_session.commit()

    # 1. Trigger execution (will pause on approval step)
    execution = await WorkflowOrchestrator.start_execution(
        db=db_session,
        workflow_id=wdef.id,
        initial_context={},
        organization_id=org.id
    )

    assert execution.status == "Waiting"

    # Find the generated ApprovalRequest
    stmt = select(ApprovalRequest).where(ApprovalRequest.workflow_execution_id == execution.id)
    res = await db_session.execute(stmt)
    approval = res.scalar_one_or_none()
    assert approval is not None
    assert approval.status == "Waiting"

    # Store IDs locally to prevent expired attribute accesses
    execution_id = execution.id
    approval_id = approval.id

    # 2. Submit Approved decision (should resume execution and complete workflow)
    await ApprovalService.submit_decision(
        db=db_session,
        approval_id=approval_id,
        user_id=str(user.id),
        vote="Approved",
        comments="Approved by Test Manager"
    )

    # Refresh execution
    stmt_exec = select(WorkflowExecution).where(WorkflowExecution.id == execution_id)
    res_exec = await db_session.execute(stmt_exec)
    execution = res_exec.scalar_one()

    # Execution is successfully completed after manual override approval resume
    assert execution.status == "Completed"

@pytest.mark.asyncio
async def test_approval_escalation_and_delegation(db_session: AsyncSession):
    user, org = await seed_agent_test_data(db_session)

    # Create manual approval request
    approval = await ApprovalService.create_approval(
        db=db_session,
        workflow_execution_id=None,
        step_name=None,
        title="Escalation Test Request",
        description="Pending review",
        assigned_approver=str(user.id),
        policy_type="Single",
        organization_id=org.id
    )

    # Store ID
    approval_id = approval.id

    # 1. Test delegation reassigns
    delegate_uuid = uuid.uuid4()
    await ApprovalDelegator.delegate(db_session, approval, str(delegate_uuid))
    assert approval.status == "Delegated"
    assert approval.assigned_approver == str(delegate_uuid)

    # 2. Test escalation updates status to Escalated if created_at is old
    # Force backdate the created_at to trigger SLA timeout
    from datetime import datetime, timedelta
    approval.created_at = datetime.utcnow() - timedelta(hours=48)
    approval.status = "Waiting"  # Reset status to Waiting to trigger checking
    db_session.add(approval)
    await db_session.commit()

    await ApprovalEscalator.run_escalation_checks(db_session)
    
    # Reload and assert
    stmt = select(ApprovalRequest).where(ApprovalRequest.id == approval_id)
    res = await db_session.execute(stmt)
    approval = res.scalar_one()
    assert approval.status == "Escalated"
    assert approval.assigned_approver == "00000000-0000-0000-0000-000000000000"
