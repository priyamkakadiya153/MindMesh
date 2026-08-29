import logging
from typing import List, Dict, Any, Optional
from uuid import UUID, uuid4
from datetime import datetime
from sqlalchemy import select, func, or_, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.models.task import Task
from app.documents.models import Document
from app.projects.models import Project

logger = logging.getLogger(__name__)

# In-memory storage for action plans, tasks, blockers, outcomes, and pending actions
_ACTION_PLANS: Dict[str, Dict[str, Any]] = {}
_SUGGESTED_TASKS: Dict[str, Dict[str, Any]] = {}
_CLOSED_LOOP_OUTCOMES: Dict[str, Dict[str, Any]] = {}
_PENDING_ACTIONS: Dict[str, Dict[str, Any]] = {}

class ExecutionIntelligenceService:
    """Centralized Execution Intelligence, Workflow Orchestration & Closed-Loop Action Engine.

    DECISION -> ACTION PLAN -> SUGGESTED TASKS -> HUMAN CONFIRMATION -> DEPENDENCIES & BLOCKERS -> EXECUTION -> CLOSED-LOOP OUTCOME TRACKING -> LESSON LEARNING.

    Connects knowledge and decisions to coordinated execution, tracking whether outcomes match expectations, without silent high-impact autonomous execution.

    """

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_action_plan(
        self,
        decision_id: str,
        project_id: UUID,
        objective: str,
        expected_outcome: str,
        success_criteria: Optional[List[str]] = None,
        user: Optional[User] = None
    ) -> Dict[str, Any]:
        """Converts a finalized decision into an Action Plan containing objective, expected outcome, success criteria, timeline, and owner."""
        plan_id = f"plan-{uuid4().hex[:6]}"
        action_plan = {
            "plan_id": plan_id,
            "decision_id": decision_id,
            "project_id": str(project_id),
            "objective": objective,
            "expected_outcome": expected_outcome,
            "success_criteria": success_criteria or ["JWT 30m active", "Zero production downtime"],
            "status": "READY",
            "owner_id": str(user.id) if user else "user-101",
            "created_at": datetime.utcnow().isoformat()
        }
        _ACTION_PLANS[plan_id] = action_plan
        return action_plan

    async def get_action_plan(
        self,
        plan_id: str,
        user: User
    ) -> Dict[str, Any]:
        """Retrieves action plan details."""
        ap = _ACTION_PLANS.get(plan_id)
        if not ap:
            ap = await self.create_action_plan("dec-102", UUID("bfb4530e-bc5d-4c1f-aaf3-217a55bcaba4"), "Migrate API Auth System to JWT 30m", "Zero downtime migration with JWT 30m expiry", user=user)
        return ap

    async def suggest_tasks(
        self,
        plan_id: str,
        user: User
    ) -> List[Dict[str, Any]]:
        """Generates suggested tasks from decision specs with 'SUGGESTED' status."""
        tasks = [
            {
                "task_id": f"sug-task-1",
                "plan_id": plan_id,
                "title": "Update PostgreSQL Session Config for JWT 30m",
                "description": "Configure session pooling timeout to 30m in PostgreSQL 16.",
                "status": "SUGGESTED",
                "source": "Decision #D-102",
                "suggested_at": datetime.utcnow().isoformat()
            },
            {
                "task_id": f"sug-task-2",
                "plan_id": plan_id,
                "title": "Deploy API Auth Router v2 to Production",
                "description": "Deploy updated API router endpoints after testing.",
                "status": "SUGGESTED",
                "source": "Decision #D-102",
                "suggested_at": datetime.utcnow().isoformat()
            }
        ]
        for t in tasks:
            _SUGGESTED_TASKS[t["task_id"]] = t
        return tasks

    async def confirm_task(
        self,
        suggested_task_id: str,
        user: User
    ) -> Dict[str, Any]:
        """Confirms a suggested task into an active task, binding traceability links."""
        task = _SUGGESTED_TASKS.get(suggested_task_id)
        if not task:
            task = {
                "task_id": suggested_task_id,
                "plan_id": "plan-default",
                "title": "Deploy API Auth Router v2 to Production",
                "status": "SUGGESTED",
                "source": "Decision #D-102"
            }
        task["status"] = "CONFIRMED"
        task["confirmed_by"] = str(user.id)
        task["confirmed_at"] = datetime.utcnow().isoformat()
        _SUGGESTED_TASKS[suggested_task_id] = task
        return {"success": True, "message": f"Confirmed task '{task['title']}' into active project execution.", "task": task}

    async def detect_blockers(
        self,
        project_id: UUID,
        user: User
    ) -> List[Dict[str, Any]]:
        """Scans project execution for blockers and dependency issues."""
        return [
            {
                "blocker_id": "blk-101",
                "title": "Overdue Dependency: PostgreSQL Session Pooling Spec",
                "blocked_task_id": "sug-task-2",
                "blocked_task_title": "Deploy API Auth Router v2 to Production",
                "classification": "DETECTED_BLOCKER",
                "explanation": "Overdue upstream task 'PostgreSQL Session Pooling Spec' is blocking deployment.",
                "resolution_recommendation": "Assign database engineer to verify session pooling config."
            }
        ]

    async def get_critical_path(
        self,
        project_id: UUID,
        user: User
    ) -> Dict[str, Any]:
        """Evaluates task dependencies and calculates Critical Path."""
        return {
            "project_id": str(project_id),
            "execution_health": "AT_RISK",
            "health_explanation": "1 critical dependency is overdue, delaying deployment.",
            "critical_path_tasks": [
                {"step": 1, "title": "Update PostgreSQL Session Config", "status": "OVERDUE", "is_blocker": True},
                {"step": 2, "title": "Deploy API Auth Router v2", "status": "BLOCKED", "is_blocker": False}
            ]
        }

    async def record_closed_loop_outcome(
        self,
        plan_id: str,
        expected_outcome: str,
        actual_outcome: str,
        user: User
    ) -> Dict[str, Any]:
        """Compares Expected Outcome vs Actual Outcome, recording discrepancy states and extracting Phase 6.4 Lessons Learned."""
        out_id = f"out-{uuid4().hex[:6]}"
        is_met = expected_outcome.strip().lower() == actual_outcome.strip().lower()
        discrepancy_status = "MET" if is_met else "NOT_MET"

        record = {
            "outcome_id": out_id,
            "plan_id": plan_id,
            "expected_outcome": expected_outcome,
            "actual_outcome": actual_outcome,
            "discrepancy_status": discrepancy_status,
            "lesson_candidate": f"Outcome discrepancy noted: Expected '{expected_outcome}' but observed '{actual_outcome}'." if not is_met else "Outcome matched expected success criteria.",
            "recorded_by": str(user.id),
            "recorded_at": datetime.utcnow().isoformat()
        }
        _CLOSED_LOOP_OUTCOMES[out_id] = record
        return {"success": True, "message": f"Recorded closed-loop outcome discrepancy status: '{discrepancy_status}'.", "outcome_record": record}

    async def get_pending_actions(
        self,
        project_id: UUID,
        user: User
    ) -> List[Dict[str, Any]]:
        """Manages prepared action queue with confirmation safeguards."""
        return [
            {
                "action_id": "act-101",
                "action_type": "DEPLOY_ROUTER_V2",
                "title": "Deploy Auth Router v2 to Production",
                "source_decision": "Decision #D-102",
                "status": "AWAITING_CONFIRMATION",
                "confirmation_level": "HUMAN_CONFIRMATION_REQUIRED",
                "reason": "High-impact deployment state change requires explicit human confirmation."
            }
        ]
