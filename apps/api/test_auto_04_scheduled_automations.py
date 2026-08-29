import asyncio
import sys
import os
from uuid import uuid4
from datetime import datetime, timedelta, timezone

# Add apps/api to path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app.automation.schedule_calculator import ScheduleCalculator
from app.actions.executors.automation_executor import CreateAutomationActionExecutor
from app.actions.executors.automation_management_executors import (
    PauseAutomationActionExecutor,
    ResumeAutomationActionExecutor,
    CancelAutomationActionExecutor,
    UpdateAutomationActionExecutor
)
from app.actions.classifier import ActionClassifier
from app.actions.registry import action_registry
from app.actions.types import ActionProposal, ActionIntentType, ActionStatus, ActionResultStatus
from app.automation.scheduled_automation_model import ScheduledAutomation

def test_schedule_calculator_types():
    now_utc = datetime.now(timezone.utc).replace(tzinfo=None)

    # 1. Daily
    next_daily = ScheduleCalculator.calculate_next_run("DAILY", time_str="9:00 AM", tz_name="Asia/Kolkata", from_utc=now_utc)
    assert next_daily > now_utc

    # 2. Weekly (Monday)
    next_weekly = ScheduleCalculator.calculate_next_run("WEEKLY", time_str="9:00 AM", day_of_week="Monday", tz_name="Asia/Kolkata", from_utc=now_utc)
    assert next_weekly > now_utc

    # 3. Weekdays
    next_weekday = ScheduleCalculator.calculate_next_run("WEEKDAYS", time_str="8:00 AM", tz_name="Asia/Kolkata", from_utc=now_utc)
    assert next_weekday > now_utc

    # 4. Monthly
    next_monthly = ScheduleCalculator.calculate_next_run("MONTHLY", time_str="9:00 AM", tz_name="Asia/Kolkata", from_utc=now_utc)
    assert next_monthly > now_utc

    print("[PASS] Test: ScheduleCalculator next-run calculations across all schedule types")

def test_natural_language_automation_classification():
    # 1. Weekly reminder
    prop1 = ActionClassifier.classify("Every Monday at 9 AM remind me to review pending tasks.")
    assert prop1 is not None
    assert prop1.intent_type == ActionIntentType.CREATE_AUTOMATION
    assert prop1.parameters.get("schedule_type") == "WEEKLY"
    assert prop1.parameters.get("day_of_week") == "Monday"
    assert prop1.parameters.get("time_str") in ["9 AM", "9:00 AM"]

    # 2. Weekly DM
    prop2 = ActionClassifier.classify("Every Friday at 5 PM message Rahul asking for the API status.")
    assert prop2 is not None
    assert prop2.intent_type == ActionIntentType.CREATE_AUTOMATION
    assert prop2.parameters.get("schedule_type") == "WEEKLY"
    assert prop2.parameters.get("day_of_week") == "Friday"
    assert prop2.parameters.get("action_type") == "SEND_DIRECT_MESSAGE"

    # 3. Weekday task
    prop3 = ActionClassifier.classify("Every weekday at 8 AM create a task to review the deployment report.")
    assert prop3 is not None
    assert prop3.intent_type == ActionIntentType.CREATE_AUTOMATION
    assert prop3.parameters.get("schedule_type") == "WEEKDAYS"
    assert prop3.parameters.get("action_type") == "CREATE_TASK"

    print("[PASS] Test: Natural language automation classification variants")

def test_ambiguous_schedule_clarification():
    prop = ActionClassifier.classify("Every Monday remind me to review the report.")
    assert prop is not None
    assert prop.status == ActionStatus.NEEDS_CLARIFICATION
    assert prop.clarification_prompt is not None and "time" in prop.clarification_prompt.lower()
    print("[PASS] Test: Ambiguous schedule missing time clarification")

def test_blocked_destructive_scheduled_action():
    prop = ActionClassifier.classify("Every Friday delete completed tasks.")
    assert prop is not None
    assert prop.status == ActionStatus.FAILED
    assert prop.parameters.get("is_blocked") is True
    print("[PASS] Test: Blocked destructive scheduled action protection")

def test_automation_lifecycle_executors():
    class DummyUser:
        id = uuid4()
        organization_id = uuid4()
        current_workspace_id = uuid4()
        email = "user@mindmesh.com"
        timezone = "Asia/Kolkata"

    class DummyAuto:
        def __init__(self):
            self.id = uuid4()
            self.user_id = DummyUser.id
            self.organization_id = DummyUser.organization_id
            self.workspace_id = DummyUser.current_workspace_id
            self.name = "Weekly Task Review"
            self.schedule_type = "WEEKLY"
            self.recurrence_rule = "every_monday"
            self.timezone = "Asia/Kolkata"
            self.status = "ACTIVE"
            self.next_run_at = datetime.now(timezone.utc) + timedelta(days=1)
            self.action_payload = {}

    dummy_auto = DummyAuto()

    class DummyDB:
        def __init__(self):
            self.added = []

        async def execute(self, stmt):
            class Res:
                def scalar_one_or_none(self):
                    return dummy_auto
                def scalars(self):
                    class SubRes:
                        def first(self):
                            return dummy_auto
                        def all(self):
                            return [dummy_auto]
                    return SubRes()
            return Res()

        def add(self, obj):
            if not getattr(obj, "id", None):
                obj.id = uuid4()
            self.added.append(obj)

        async def commit(self):
            pass
        async def refresh(self, obj):
            pass
        async def rollback(self):
            pass

    db = DummyDB()

    # 1. Create Automation
    proposal_create = ActionProposal(
        proposal_id=f"prop-create-{uuid4().hex[:6]}",
        intent_type=ActionIntentType.CREATE_AUTOMATION,
        title="Create Automation: Weekly Task Review",
        parameters={
            "name": "Weekly Task Review",
            "action_type": "CREATE_REMINDER",
            "action_payload": {"reminder_text": "Review pending tasks"},
            "schedule_type": "WEEKLY",
            "day_of_week": "Monday",
            "time_str": "9:00 AM"
        },
        workspace_id=str(DummyUser.current_workspace_id),
        user_id=str(DummyUser.id),
        confirmation_required=True,
        status=ActionStatus.CONFIRMED
    )

    res_create = asyncio.run(CreateAutomationActionExecutor().execute(proposal_create, DummyUser(), db))
    assert res_create.status == ActionResultStatus.SUCCESS

    # 2. Pause Automation
    proposal_pause = ActionProposal(
        proposal_id=f"prop-pause-{uuid4().hex[:6]}",
        intent_type=ActionIntentType.PAUSE_AUTOMATION,
        title="Pause Automation",
        parameters={"automation_id": str(dummy_auto.id)},
        workspace_id=str(DummyUser.current_workspace_id),
        user_id=str(DummyUser.id),
        confirmation_required=True,
        status=ActionStatus.CONFIRMED
    )
    res_pause = asyncio.run(PauseAutomationActionExecutor().execute(proposal_pause, DummyUser(), db))
    assert res_pause.status == ActionResultStatus.SUCCESS
    assert dummy_auto.status == "PAUSED"

    # 3. Resume Automation
    proposal_resume = ActionProposal(
        proposal_id=f"prop-resume-{uuid4().hex[:6]}",
        intent_type=ActionIntentType.RESUME_AUTOMATION,
        title="Resume Automation",
        parameters={"automation_id": str(dummy_auto.id)},
        workspace_id=str(DummyUser.current_workspace_id),
        user_id=str(DummyUser.id),
        confirmation_required=True,
        status=ActionStatus.CONFIRMED
    )
    res_resume = asyncio.run(ResumeAutomationActionExecutor().execute(proposal_resume, DummyUser(), db))
    assert res_resume.status == ActionResultStatus.SUCCESS
    assert dummy_auto.status == "ACTIVE"

    # 4. Cancel Automation
    proposal_cancel = ActionProposal(
        proposal_id=f"prop-cancel-{uuid4().hex[:6]}",
        intent_type=ActionIntentType.CANCEL_AUTOMATION,
        title="Cancel Automation",
        parameters={"automation_id": str(dummy_auto.id)},
        workspace_id=str(DummyUser.current_workspace_id),
        user_id=str(DummyUser.id),
        confirmation_required=True,
        status=ActionStatus.CONFIRMED
    )
    res_cancel = asyncio.run(CancelAutomationActionExecutor().execute(proposal_cancel, DummyUser(), db))
    assert res_cancel.status == ActionResultStatus.SUCCESS
    assert dummy_auto.status == "CANCELLED"

    print("[PASS] Test: Automation lifecycle executors (Create, Pause, Resume, Cancel)")

if __name__ == "__main__":
    print("Running AUTO-04 Scheduled Automations Test Suite...")
    test_schedule_calculator_types()
    test_natural_language_automation_classification()
    test_ambiguous_schedule_clarification()
    test_blocked_destructive_scheduled_action()
    test_automation_lifecycle_executors()
    print("\nALL AUTO-04 EXECUTION TESTS PASSED SUCCESSFULLY!")
