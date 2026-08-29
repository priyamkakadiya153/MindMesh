import asyncio
import sys
import os
from datetime import datetime, timezone, timedelta
from uuid import uuid4

# Add apps/api to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../apps/api')))

import app.models
from app.documents.models import Document
from app.models.task import Task
from app.actions.policy import ActionSafetyPolicy, ActionRiskLevel
from app.actions.safety_guard import ActionSafetyGuard
from app.actions.types import ActionIntentType, ActionProposal, ActionResult, ActionResultStatus
from app.actions.registry import action_registry
from app.actions.classifier import ActionClassifier

def test_action_safety_policy():
    # 1. Level 0 Read-Only
    p0 = ActionSafetyPolicy.evaluate(ActionIntentType.CREATE_TASK, {"is_read_only": True})
    assert p0.risk_level == ActionRiskLevel.LEVEL_0_READ_ONLY
    assert p0.confirmation_required is False
    assert p0.is_blocked is False
    print("[PASS] Policy test Level 0 Read-Only")

    # 2. Level 1 Low-Risk Reversible
    p1 = ActionSafetyPolicy.evaluate(ActionIntentType.CREATE_TASK)
    assert p1.risk_level == ActionRiskLevel.LEVEL_1_LOW_RISK
    assert p1.confirmation_required is True
    assert p1.action_button_label == "Create Task"
    print("[PASS] Policy test Level 1 Low-Risk Reversible")

    # 3. Level 2 Externally Visible
    p2 = ActionSafetyPolicy.evaluate(ActionIntentType.SEND_DIRECT_MESSAGE)
    assert p2.risk_level == ActionRiskLevel.LEVEL_2_EXTERNAL
    assert p2.confirmation_required is True
    assert p2.action_button_label == "Send Message"
    print("[PASS] Policy test Level 2 Externally Visible")

    # 4. Level 3 Destructive (Blocked)
    p3 = ActionSafetyPolicy.evaluate(ActionIntentType.DELETE_DOCUMENT)
    assert p3.risk_level == ActionRiskLevel.LEVEL_3_DESTRUCTIVE
    assert p3.is_blocked is True
    print("[PASS] Policy test Level 3 Destructive Blocked")

def test_safety_guard_validations():
    # 1. Expiration test
    old_prop = ActionProposal(
        proposal_id="prop-expired-1",
        intent_type=ActionIntentType.CREATE_TASK,
        title="Test",
        created_at=datetime.now(timezone.utc) - timedelta(minutes=20)
    )
    is_valid, err = ActionSafetyGuard.validate_expiration(old_prop, ttl_minutes=15)
    assert is_valid is False
    assert "expired" in err.lower()
    print("[PASS] Safety Guard Expiration test")

    # 2. Workspace scope test
    class DummyUser:
        id = uuid4()
        current_workspace_id = uuid4()

    ws_prop = ActionProposal(
        proposal_id="prop-ws-1",
        intent_type=ActionIntentType.CREATE_TASK,
        title="Test",
        workspace_id=str(uuid4()) # Different workspace ID
    )
    is_valid_ws, ws_err = ActionSafetyGuard.validate_workspace_scope(ws_prop, DummyUser())
    assert is_valid_ws is False
    assert "workspace mismatch" in ws_err.lower()
    print("[PASS] Safety Guard Workspace Scope test")

def test_destructive_classifier_blocking():
    prop = ActionClassifier.classify("Delete the main workspace project.")
    assert prop is not None
    assert prop.intent_type == ActionIntentType.DELETE_DOCUMENT
    assert prop.parameters.get("is_blocked") is True
    print("[PASS] Destructive Action Classifier Blocking test")

def test_idempotency_guard():
    class DummyUser:
        id = uuid4()
        organization_id = uuid4()
        current_workspace_id = uuid4()
        email = "test@mindmesh.com"

    dummy_prop = ActionProposal(
        proposal_id="prop-idempotency-123",
        intent_type=ActionIntentType.CREATE_TASK,
        title="Idempotent Task",
        workspace_id=str(DummyUser.current_workspace_id),
        parameters={"title": "Idempotent Task"}
    )

    class DummyDB:
        async def execute(self, stmt):
            class DummyResult:
                def scalar_one_or_none(self): return Task(id=uuid4(), title="Test Task")
                def scalars(self):
                    class DummyScalars:
                        def first(self): return Task(id=uuid4(), title="Test Task")
                        def scalar_one_or_none(self): return None
                    return DummyScalars()
            return DummyResult()
        def add(self, obj): obj.id = uuid4()
        async def flush(self): pass
        async def refresh(self, obj): pass
        async def commit(self): pass
        async def rollback(self): pass

    # First dispatch
    res1 = asyncio.run(action_registry.dispatch(dummy_prop, DummyUser(), DummyDB()))
    assert res1.status == ActionResultStatus.SUCCESS

    # Second dispatch with SAME proposal_id (double click simulation)
    res2 = asyncio.run(action_registry.dispatch(dummy_prop, DummyUser(), DummyDB()))
    assert res2 == res1 # Returns cached result without executing twice!
    print("[PASS] Idempotency Guard Double-Click Prevention test")

if __name__ == "__main__":
    print("Running AUTO-06 Action Confirmation & Safety Test Suite...")
    test_action_safety_policy()
    test_safety_guard_validations()
    test_destructive_classifier_blocking()
    test_idempotency_guard()
    print("ALL AUTO-06 BACKEND TESTS PASSED SUCCESSFULLY!")
