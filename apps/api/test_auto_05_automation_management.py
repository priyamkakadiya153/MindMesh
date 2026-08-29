import asyncio
import sys
import os
from uuid import uuid4
from datetime import datetime, timedelta, timezone

# Add apps/api to path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app.automation.automation_resolver import AutomationResolver
from app.actions.executors.automation_management_executors import (
    PauseAutomationActionExecutor,
    ResumeAutomationActionExecutor,
    CancelAutomationActionExecutor,
    UpdateAutomationActionExecutor
)
from app.actions.classifier import ActionClassifier
from app.actions.types import ActionProposal, ActionIntentType, ActionStatus, ActionResultStatus
from app.automation.scheduled_automation_model import ScheduledAutomation

class DummyUser:
    id = uuid4()
    organization_id = uuid4()
    current_workspace_id = uuid4()
    email = "user@mindmesh.com"
    timezone = "Asia/Kolkata"

class DummyAuto:
    def __init__(self, name="Weekly Task Review", schedule_type="WEEKLY", recurrence_rule="every_monday", status="ACTIVE", recipient="Rahul", msg="Review pending tasks"):
        self.id = uuid4()
        self.user_id = DummyUser.id
        self.organization_id = DummyUser.organization_id
        self.workspace_id = DummyUser.current_workspace_id
        self.name = name
        self.schedule_type = schedule_type
        self.recurrence_rule = recurrence_rule
        self.timezone = "Asia/Kolkata"
        self.status = status
        self.next_run_at = datetime.now(timezone.utc) + timedelta(days=1)
        self.action_payload = {"recipient_name": recipient, "message_body": msg, "reminder_text": msg, "title": name}
        self.created_at = datetime.now(timezone.utc)
        self.last_run_at = datetime.now(timezone.utc) - timedelta(days=2)
        self.last_run_status = "SUCCESS"

class DummyDB:
    def __init__(self, automations=None):
        self.automations = automations or []

    async def execute(self, stmt):
        automations = self.automations
        class Res:
            def scalar_one_or_none(self):
                return automations[0] if automations else None
            def scalars(self):
                class SubRes:
                    def first(self):
                        return automations[0] if automations else None
                    def all(self):
                        return automations
                return SubRes()
        return Res()

    def add(self, obj):
        pass
    async def commit(self):
        pass
    async def refresh(self, obj):
        pass
    async def rollback(self):
        pass

def test_automation_resolver_ordinal_and_name_matching():
    auto1 = DummyAuto(name="Weekly Task Review", recurrence_rule="every_monday")
    auto2 = DummyAuto(name="Friday Status Report", recurrence_rule="every_friday")
    db = DummyDB([auto1, auto2])

    # 1. Resolve first one
    res1, err1 = asyncio.run(AutomationResolver.resolve("first one", DummyUser.id, db))
    assert res1 is not None and res1.id == auto1.id

    # 2. Resolve second one
    res2, err2 = asyncio.run(AutomationResolver.resolve("second one", DummyUser.id, db))
    assert res2 is not None and res2.id == auto2.id

    # 3. Resolve by name substring "friday"
    res_fri, err_fri = asyncio.run(AutomationResolver.resolve("Friday Status Report", DummyUser.id, db))
    assert res_fri is not None and res_fri.id == auto2.id

    print("[PASS] Test: AutomationResolver ordinal & name resolution")

def test_pause_and_resume_executors():
    auto = DummyAuto(name="Weekly Task Review", status="ACTIVE")
    db = DummyDB([auto])

    # 1. Pause
    proposal_pause = ActionProposal(
        proposal_id=f"prop-pause-{uuid4().hex[:6]}",
        intent_type=ActionIntentType.PAUSE_AUTOMATION,
        title="Pause Automation",
        parameters={"automation_id": str(auto.id)},
        workspace_id=str(DummyUser.current_workspace_id),
        user_id=str(DummyUser.id),
        confirmation_required=True,
        status=ActionStatus.CONFIRMED
    )
    res_pause = asyncio.run(PauseAutomationActionExecutor().execute(proposal_pause, DummyUser(), db))
    assert res_pause.status == ActionResultStatus.SUCCESS
    assert auto.status == "PAUSED"

    # 2. Resume
    proposal_resume = ActionProposal(
        proposal_id=f"prop-resume-{uuid4().hex[:6]}",
        intent_type=ActionIntentType.RESUME_AUTOMATION,
        title="Resume Automation",
        parameters={"automation_id": str(auto.id)},
        workspace_id=str(DummyUser.current_workspace_id),
        user_id=str(DummyUser.id),
        confirmation_required=True,
        status=ActionStatus.CONFIRMED
    )
    res_resume = asyncio.run(ResumeAutomationActionExecutor().execute(proposal_resume, DummyUser(), db))
    assert res_resume.status == ActionResultStatus.SUCCESS
    assert auto.status == "ACTIVE"

    print("[PASS] Test: Pause and Resume automation executors")

def test_update_automation_schedule_and_payload_executors():
    auto = DummyAuto(name="Friday Status Report", schedule_type="WEEKLY", recurrence_rule="every_friday", recipient="Rahul")
    db = DummyDB([auto])

    # 1. Update Schedule (Tuesday at 10 AM)
    proposal_update_sched = ActionProposal(
        proposal_id=f"prop-upd-sched-{uuid4().hex[:6]}",
        intent_type=ActionIntentType.UPDATE_AUTOMATION,
        title="Update Automation",
        parameters={
            "automation_id": str(auto.id),
            "day_of_week": "Tuesday",
            "time_str": "10:00 AM",
            "schedule_type": "WEEKLY"
        },
        workspace_id=str(DummyUser.current_workspace_id),
        user_id=str(DummyUser.id),
        confirmation_required=True,
        status=ActionStatus.CONFIRMED
    )
    res_sched = asyncio.run(UpdateAutomationActionExecutor().execute(proposal_update_sched, DummyUser(), db))
    assert res_sched.status == ActionResultStatus.SUCCESS
    assert auto.recurrence_rule == "every_tuesday"

    # 2. Update Recipient ("Dhruvil") & Message Body ("Please send me the deployment status")
    proposal_update_payload = ActionProposal(
        proposal_id=f"prop-upd-pay-{uuid4().hex[:6]}",
        intent_type=ActionIntentType.UPDATE_AUTOMATION,
        title="Update Automation",
        parameters={
            "automation_id": str(auto.id),
            "new_recipient_name": "Dhruvil",
            "new_message_body": "Please send me the deployment status."
        },
        workspace_id=str(DummyUser.current_workspace_id),
        user_id=str(DummyUser.id),
        confirmation_required=True,
        status=ActionStatus.CONFIRMED
    )
    res_pay = asyncio.run(UpdateAutomationActionExecutor().execute(proposal_update_payload, DummyUser(), db))
    assert res_pay.status == ActionResultStatus.SUCCESS
    assert auto.action_payload.get("recipient_name") == "Dhruvil"
    assert auto.action_payload.get("message_body") == "Please send me the deployment status."

    print("[PASS] Test: Update automation schedule, recipient, and message payload executors")

def test_cancel_automation_executor():
    auto = DummyAuto(name="Friday Status Report", status="ACTIVE")
    db = DummyDB([auto])

    proposal_cancel = ActionProposal(
        proposal_id=f"prop-cancel-{uuid4().hex[:6]}",
        intent_type=ActionIntentType.CANCEL_AUTOMATION,
        title="Cancel Automation",
        parameters={"automation_id": str(auto.id)},
        workspace_id=str(DummyUser.current_workspace_id),
        user_id=str(DummyUser.id),
        confirmation_required=True,
        status=ActionStatus.CONFIRMED
    )
    res_cancel = asyncio.run(CancelAutomationActionExecutor().execute(proposal_cancel, DummyUser(), db))
    assert res_cancel.status == ActionResultStatus.SUCCESS
    assert auto.status == "CANCELLED"
    assert auto.next_run_at is None

    print("[PASS] Test: Cancel automation executor")

if __name__ == "__main__":
    print("Running AUTO-05 Conversational Automation Management Test Suite...")
    test_automation_resolver_ordinal_and_name_matching()
    test_pause_and_resume_executors()
    test_update_automation_schedule_and_payload_executors()
    test_cancel_automation_executor()
    print("\nALL AUTO-05 EXECUTION TESTS PASSED SUCCESSFULLY!")
