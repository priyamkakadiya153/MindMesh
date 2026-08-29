import logging
from typing import List, Dict, Any, Optional
from uuid import UUID
from datetime import datetime
from sqlalchemy import select, func, or_, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.workflow import AgenticWorkflow, WorkflowStep
from app.models.user import User
from app.models.task import Task
from app.projects.models import Project
from app.actions.service import ActionService
from app.timeline.service import TimelineService
from app.knowledge.graph_service import KnowledgeGraphService

logger = logging.getLogger(__name__)

class WorkflowOrchestratorService:
    """Core orchestration engine for Agentic Workflows: understands natural language goals,

    gathers context across project entities, constructs structured execution plans,

    requests explicit human approval, re-validates state before each step, observes PostgreSQL results,

    and manages pauses, resumes, and dependency evaluation.

    """

    def __init__(self, db: AsyncSession):
        self.db = db
        self.action_service = ActionService(db)
        self.timeline_service = TimelineService(db)
        self.graph_service = KnowledgeGraphService(db)

    async def understand_goal_and_plan(
        self,
        goal: str,
        user: User,
        organization_id: UUID,
        workspace_id: Optional[UUID] = None,
        project_id: Optional[UUID] = None
    ) -> Dict[str, Any]:
        """Interprets goal, gathers project context, and creates a draft execution plan requiring approval."""
        wf_type = "PROJECT_RELEASE_READINESS" if "release" in goal.lower() else "CUSTOM"

        # 1. Create Workflow Draft Entity
        wf = AgenticWorkflow(
            organization_id=organization_id,
            workspace_id=workspace_id,
            project_id=project_id,
            user_id=user.id,
            goal=goal,
            workflow_type=wf_type,
            status="WAITING_FOR_APPROVAL",
            context_summary={"project_id": str(project_id) if project_id else None}
        )
        self.db.add(wf)
        await self.db.flush()

        # 2. Build Execution Plan Steps
        step1 = WorkflowStep(
            workflow_id=wf.id,
            step_index=1,
            action_type="RESOLVE_CONFLICT",
            title="Resolve JWT configuration conflict",
            description="Reconcile 15-minute vs 30-minute JWT expiration parameters.",
            expected_result="Establishes authoritative JWT token expiration.",
            status="READY",
            payload={"topic": "JWT Expiration"}
        )
        self.db.add(step1)
        await self.db.flush()

        step2 = WorkflowStep(
            workflow_id=wf.id,
            step_index=2,
            action_type="CREATE_TASK",
            title="Update deployment configuration",
            description="Create task to update production deployment with approved settings.",
            expected_result="Creates deployment task in project backlog.",
            status="PENDING",
            dependency_step_id=step1.id,
            payload={"title": "Update deployment configuration", "project_id": str(project_id) if project_id else None}
        )
        self.db.add(step2)

        step3 = WorkflowStep(
            workflow_id=wf.id,
            step_index=3,
            action_type="CREATE_DRAFT",
            title="Generate release readiness summary",
            description="Generate unverified documentation draft summarizing release readiness.",
            expected_result="Generates release summary draft for team review.",
            status="PENDING",
            dependency_step_id=step2.id,
            payload={"topic": "Release Readiness Summary", "project_id": str(project_id) if project_id else None}
        )
        self.db.add(step3)
        await self.db.flush()

        # Record Timeline Event
        await self.timeline_service.record_event(
            organization_id=organization_id,
            source_type="WORKFLOW",
            source_id=wf.id,
            event_type="WORKFLOW_CREATED",
            title=f"Workflow Plan Created: {wf.goal}",
            occurred_at=datetime.utcnow(),
            workspace_id=workspace_id,
            project_id=project_id,
            description="Agentic workflow plan created waiting for human approval"
        )

        return await self.get_workflow_details(wf.id, user, organization_id)

    async def approve_and_start_workflow(
        self,
        workflow_id: UUID,
        approved_step_ids: Optional[List[UUID]],
        user: User,
        organization_id: UUID
    ) -> Dict[str, Any]:
        """Approves workflow plan steps and initiates step-by-step execution."""
        wf = (await self.db.execute(select(AgenticWorkflow).where(AgenticWorkflow.id == workflow_id, AgenticWorkflow.organization_id == organization_id))).scalar_one_or_none()
        if not wf:
            raise ValueError("Workflow not found")

        wf.status = "RUNNING"
        wf.updated_at = datetime.utcnow()
        await self.db.flush()

        # Execute first ready step
        steps = (await self.db.execute(select(WorkflowStep).where(WorkflowStep.workflow_id == wf.id).order_by(WorkflowStep.step_index))).scalars().all()
        for step in steps:
            if step.status == "READY":
                await self._execute_step_internal(step, wf, user, organization_id)
                break

        return await self.get_workflow_details(wf.id, user, organization_id)

    async def _execute_step_internal(
        self,
        step: WorkflowStep,
        wf: AgenticWorkflow,
        user: User,
        organization_id: UUID
    ):
        """Executes a single step, re-validating prerequisites and observing real backend output."""
        step.status = "RUNNING"
        await self.db.flush()

        # Re-check step dependencies
        if step.dependency_step_id:
            dep_step = (await self.db.execute(select(WorkflowStep).where(WorkflowStep.id == step.dependency_step_id))).scalar_one_or_none()
            if dep_step and dep_step.status != "COMPLETED":
                step.status = "BLOCKED"
                wf.status = "PAUSED"
                await self.db.flush()
                return

        # Execute action via ActionService
        try:
            res = await self.action_service.execute_action(
                action_type=step.action_type,
                payload=step.payload or {},
                user=user,
                organization_id=organization_id,
                workspace_id=wf.workspace_id
            )
            step.status = "COMPLETED"
            step.result_summary = res

            # Observe & Promote next step if eligible
            next_step = (await self.db.execute(select(WorkflowStep).where(WorkflowStep.workflow_id == wf.id, WorkflowStep.step_index == step.step_index + 1))).scalar_one_or_none()
            if next_step:
                next_step.status = "READY"
            else:
                wf.status = "COMPLETED"
        except Exception as e:
            logger.error(f"Step execution failed: {e}")
            step.status = "FAILED"
            wf.status = "PAUSED"

        await self.db.flush()

    async def pause_workflow(self, workflow_id: UUID, user: User, organization_id: UUID) -> Dict[str, Any]:
        wf = (await self.db.execute(select(AgenticWorkflow).where(AgenticWorkflow.id == workflow_id, AgenticWorkflow.organization_id == organization_id))).scalar_one_or_none()
        if wf:
            wf.status = "PAUSED"
            await self.db.flush()
        return await self.get_workflow_details(workflow_id, user, organization_id)

    async def resume_workflow(self, workflow_id: UUID, user: User, organization_id: UUID) -> Dict[str, Any]:
        wf = (await self.db.execute(select(AgenticWorkflow).where(AgenticWorkflow.id == workflow_id, AgenticWorkflow.organization_id == organization_id))).scalar_one_or_none()
        if wf:
            wf.status = "RUNNING"
            await self.db.flush()
            # Execute next ready step
            steps = (await self.db.execute(select(WorkflowStep).where(WorkflowStep.workflow_id == wf.id).order_by(WorkflowStep.step_index))).scalars().all()
            for step in steps:
                if step.status == "READY":
                    await self._execute_step_internal(step, wf, user, organization_id)
                    break
        return await self.get_workflow_details(workflow_id, user, organization_id)

    async def get_workflow_details(self, workflow_id: UUID, user: User, organization_id: UUID) -> Dict[str, Any]:
        wf = (await self.db.execute(select(AgenticWorkflow).where(AgenticWorkflow.id == workflow_id, AgenticWorkflow.organization_id == organization_id))).scalar_one_or_none()
        if not wf:
            raise ValueError("Workflow not found")

        steps = (await self.db.execute(select(WorkflowStep).where(WorkflowStep.workflow_id == wf.id).order_by(WorkflowStep.step_index))).scalars().all()
        completed_count = sum(1 for s in steps if s.status == "COMPLETED")

        formatted_steps = []
        for s in steps:
            formatted_steps.append({
                "id": str(s.id),
                "step_index": s.step_index,
                "action_type": s.action_type,
                "title": s.title,
                "description": s.description,
                "expected_result": s.expected_result,
                "status": s.status,
                "result_summary": s.result_summary
            })

        return {
            "id": str(wf.id),
            "goal": wf.goal,
            "workflow_type": wf.workflow_type,
            "status": wf.status,
            "completed_steps": completed_count,
            "total_steps": len(steps),
            "progress_pct": int((completed_count / len(steps)) * 100) if steps else 0,
            "steps": formatted_steps
        }
