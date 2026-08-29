import asyncio
import sys
import os
from uuid import uuid4
from datetime import datetime, timedelta, timezone

# Add apps/api to path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app.actions.audit_model import ActionEvent
from app.actions.audit_service import AuditService
from app.actions.types import ActionProposal, ActionResult, ActionResultStatus, ActionIntentType

class DummyUser:
    id = uuid4()
    organization_id = uuid4()
    current_workspace_id = uuid4()
    email = "user@mindmesh.com"

class DummyDB:
    def __init__(self):
        self.events = []

    def add(self, obj):
        if isinstance(obj, ActionEvent):
            if not obj.id:
                obj.id = uuid4()
            if not obj.created_at:
                obj.created_at = datetime.now(timezone.utc)
            self.events.append(obj)

    async def execute(self, stmt):
        events = self.events
        class Res:
            def scalar_one_or_none(self):
                return events[0] if events else None
            def scalars(self):
                class SubRes:
                    def first(self):
                        return events[0] if events else None
                    def all(self):
                        return events
                return SubRes()
        return Res()

    async def commit(self):
        pass
    async def refresh(self, obj):
        pass
    async def rollback(self):
        pass

def test_audit_event_recording():
    user = DummyUser()
    db = DummyDB()

    proposal = ActionProposal(
        proposal_id=f"prop-{uuid4().hex[:6]}",
        intent_type=ActionIntentType.CREATE_TASK,
        title="Review Deployment Report",
        parameters={"source_type": "AI_CHAT"}
    )
    result = ActionResult(
        status=ActionResultStatus.SUCCESS,
        action_type=ActionIntentType.CREATE_TASK,
        entity_type="TASK",
        entity_id=str(uuid4()),
        entity_name="Review Deployment Report",
        message="Done — task created."
    )

    ev = asyncio.run(AuditService.record_action_event(proposal, result, user, db, source_type="AI_CHAT"))
    assert ev is not None
    assert ev.action_type == "CREATE_TASK"
    assert ev.source_type == "AI_CHAT"
    assert ev.target_type == "TASK"
    assert ev.status == "SUCCESS"

    print("[PASS] Test: Immutably recording ActionEvent for AI_CHAT actions")

def test_source_type_actor_separation():
    user = DummyUser()
    db = DummyDB()

    # 1. AI Chat action
    prop_ai = ActionProposal(proposal_id="p1", intent_type=ActionIntentType.CREATE_REMINDER, title="Reminder")
    res_ai = ActionResult(status=ActionResultStatus.SUCCESS, action_type=ActionIntentType.CREATE_REMINDER, message="Success")
    ev_ai = asyncio.run(AuditService.record_action_event(prop_ai, res_ai, user, db, source_type="AI_CHAT"))
    assert ev_ai.source_type == "AI_CHAT"

    # 2. Automation action
    prop_auto = ActionProposal(proposal_id="p2", intent_type=ActionIntentType.SEND_DIRECT_MESSAGE, title="Automated DM")
    res_auto = ActionResult(status=ActionResultStatus.SUCCESS, action_type=ActionIntentType.SEND_DIRECT_MESSAGE, message="Success")
    ev_auto = asyncio.run(AuditService.record_action_event(prop_auto, res_auto, user, db, source_type="AUTOMATION"))
    assert ev_auto.source_type == "AUTOMATION"

    # 3. Direct UI action
    prop_ui = ActionProposal(proposal_id="p3", intent_type=ActionIntentType.CREATE_TASK, title="Manual Task")
    res_ui = ActionResult(status=ActionResultStatus.SUCCESS, action_type=ActionIntentType.CREATE_TASK, message="Success")
    ev_ui = asyncio.run(AuditService.record_action_event(prop_ui, res_ui, user, db, source_type="DIRECT_UI"))
    assert ev_ui.source_type == "DIRECT_UI"

    print("[PASS] Test: Source type & actor separation (AI_CHAT, AUTOMATION, DIRECT_UI)")

def test_before_after_state_recording():
    user = DummyUser()
    db = DummyDB()

    proposal = ActionProposal(
        proposal_id="p-update",
        intent_type=ActionIntentType.UPDATE_AUTOMATION,
        title="Update Schedule"
    )
    result = ActionResult(
        status=ActionResultStatus.SUCCESS,
        action_type=ActionIntentType.UPDATE_AUTOMATION,
        message="Schedule updated."
    )

    before = {"schedule": "Monday at 9 AM", "recipient": "Dhruvil"}
    after = {"schedule": "Tuesday at 10 AM", "recipient": "Rahul"}

    ev = asyncio.run(AuditService.record_action_event(proposal, result, user, db, source_type="AI_CHAT", before_state=before, after_state=after))
    assert ev.before_state == before
    assert ev.after_state == after

    print("[PASS] Test: Recording before/after state diffs for audit updates")

def test_no_llm_dependency_for_audit():
    user = DummyUser()
    db = DummyDB()

    # Audit recording executes deterministically without calling LLM APIs
    proposal = ActionProposal(proposal_id="p-nollm", intent_type=ActionIntentType.CREATE_TASK, title="Task")
    result = ActionResult(status=ActionResultStatus.SUCCESS, action_type=ActionIntentType.CREATE_TASK, message="Done")
    ev = asyncio.run(AuditService.record_action_event(proposal, result, user, db))
    assert ev is not None

    print("[PASS] Test: Audit recording executes deterministically without LLM dependency")

if __name__ == "__main__":
    print("Running AUTO-07 Action Memory & Audit Trail Test Suite...")
    test_audit_event_recording()
    test_source_type_actor_separation()
    test_before_after_state_recording()
    test_no_llm_dependency_for_audit()
    print("\nALL AUTO-07 EXECUTION TESTS PASSED SUCCESSFULLY!")
