import pytest
import uuid
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.automation.approval.models import WorkflowDefinition, WorkflowExecution, ApprovalRequest
from app.automation.workflow.orchestrator import WorkflowOrchestrator
from app.automation.approval.service import ApprovalService
from app.automation.events.publisher import EventPublisher
from app.automation.events.dispatcher import EventDispatcher
from tests.agents.test_sdk import seed_agent_test_data

class MockSessionContext:
    def __init__(self, session):
        self.session = session
    async def __aenter__(self):
        return self.session
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass

@pytest.mark.asyncio
async def test_workflow_1_e2e_approvals(db_session: AsyncSession):
    """Workflow 1: User Request -> AI Planner -> approval -> completed."""
    user, org = await seed_agent_test_data(db_session)

    # 1. Define workflow DAG with approval step
    definition = {
        "trigger": {"type": "manual"},
        "steps": [
            {
                "name": "approval_node",
                "type": "human_approval",
                "title": "Ingestion Signoff",
                "assigned_approver": str(user.id)
            },
            {
                "name": "finalize_node",
                "type": "sequential",
                "dependencies": ["approval_node"]
            }
        ]
    }

    wdef = WorkflowDefinition(
        name="Ingestion E2E Pipeline",
        definition=definition,
        organization_id=org.id,
        is_active=True
    )
    db_session.add(wdef)
    await db_session.commit()

    # 2. Trigger execution (runs step 1 and pauses)
    execution = await WorkflowOrchestrator.start_execution(
        db=db_session,
        workflow_id=wdef.id,
        initial_context={},
        organization_id=org.id
    )

    assert execution.status == "Waiting"

    # Find approval
    stmt = select(ApprovalRequest).where(ApprovalRequest.workflow_execution_id == execution.id)
    res = await db_session.execute(stmt)
    approval = res.scalar_one()
    assert approval.status == "Waiting"

    exec_id = execution.id
    app_id = approval.id

    # 3. User submits manual override approval (should resume and complete pipeline)
    await ApprovalService.submit_decision(
        db=db_session,
        approval_id=app_id,
        user_id=str(user.id),
        vote="Approved",
        comments="Signoff OK"
    )
    await db_session.commit()

    # Refresh execution status
    stmt_exec = select(WorkflowExecution).where(WorkflowExecution.id == exec_id)
    res_exec = await db_session.execute(stmt_exec)
    execution = res_exec.scalar_one()

    # Successfully completes the workflow run
    assert execution.status == "Completed"

@pytest.mark.asyncio
async def test_workflow_2_e2e_event_rag(db_session: AsyncSession):
    """Workflow 2: Document uploaded event -> auto trigger parsing RAG response."""
    user, org = await seed_agent_test_data(db_session)

    # Patch dispatcher Session constructor to share the test session
    import app.automation.events.dispatcher
    original_session_local = app.automation.events.dispatcher.AsyncSessionLocal
    app.automation.events.dispatcher.AsyncSessionLocal = lambda: MockSessionContext(db_session)
    EventDispatcher.start_listening()

    # Create workflow subscribed to document_uploaded
    definition = {
        "trigger": {"type": "event", "event_type": "document_uploaded"},
        "steps": [
            {"name": "index_document", "type": "sequential"}
        ]
    }

    wdef = WorkflowDefinition(
        name="Auto Index Pipeline",
        definition=definition,
        organization_id=org.id,
        is_active=True
    )
    db_session.add(wdef)
    await db_session.commit()

    # 1. Fire document uploaded event (triggers pipeline)
    await EventPublisher.publish_event(
        event_type="document_uploaded",
        payload={"doc_title": "architecture_review.pdf"},
        organization_id=org.id,
        db=db_session
    )

    # 2. Check spawned execution
    stmt = select(WorkflowExecution).where(WorkflowExecution.workflow_id == wdef.id)
    res = await db_session.execute(stmt)
    execution = res.scalar_one_or_none()

    assert execution is not None
    assert execution.status == "Completed"
    assert execution.context["doc_title"] == "architecture_review.pdf"

    # Restore session patch
    app.automation.events.dispatcher.AsyncSessionLocal = original_session_local
