import asyncio
import sys
import os
from uuid import uuid4
from datetime import datetime, timedelta, timezone

# Add apps/api to path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app.actions.policy import ActionSafetyPolicy, ActionRiskLevel
from app.actions.safety_guard import ActionSafetyGuard
from app.actions.types import ActionProposal, ActionIntentType, ActionStatus, ActionResultStatus, ActionConfirmRequest
from app.actions.router import confirm_action_proposal, _EXECUTED_PROPOSALS

class DummyUser:
    id = uuid4()
    organization_id = uuid4()
    current_workspace_id = uuid4()
    email = "user@mindmesh.com"

class DummyDB:
    def __init__(self):
        self.added = []

    async def execute(self, stmt):
        class Res:
            def scalar_one_or_none(self):
                return None
            def scalars(self):
                class SubRes:
                    def first(self):
                        return None
                    def all(self):
                        return []
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

def test_action_safety_policy_evaluation():
    # 1. Level 1 Internal Mutation
    pol_task = ActionSafetyPolicy.evaluate(ActionIntentType.CREATE_TASK)
    assert pol_task.risk_level == ActionRiskLevel.LEVEL_1_LOW_RISK
    assert pol_task.confirmation_required is True
    assert pol_task.action_button_label == "Create Task"

    # 2. Level 2 External Mutation
    pol_dm = ActionSafetyPolicy.evaluate(ActionIntentType.SEND_DIRECT_MESSAGE)
    assert pol_dm.risk_level == ActionRiskLevel.LEVEL_2_EXTERNAL
    assert pol_dm.confirmation_required is True
    assert pol_dm.action_button_label == "Send Message"

    # 3. Level 3 Destructive Action
    pol_del = ActionSafetyPolicy.evaluate(ActionIntentType.DELETE_DOCUMENT)
    assert pol_del.risk_level == ActionRiskLevel.LEVEL_3_DESTRUCTIVE
    assert pol_del.is_blocked is True

    # 4. Level 0 Read-Only Query
    pol_read = ActionSafetyPolicy.evaluate(ActionIntentType.CREATE_TASK, parameters={"is_read_only": True})
    assert pol_read.risk_level == ActionRiskLevel.LEVEL_0_READ_ONLY
    assert pol_read.confirmation_required is False

    print("[PASS] Test: ActionSafetyPolicy risk classification & button labels")

def test_proposal_expiration_validation():
    user = DummyUser()
    
    # 1. Fresh proposal (< 15 mins)
    fresh_prop = ActionProposal(
        proposal_id="prop-fresh",
        intent_type=ActionIntentType.CREATE_TASK,
        title="Fresh Task",
        created_at=datetime.now(timezone.utc) - timedelta(minutes=5)
    )
    is_valid_fresh, err_fresh = ActionSafetyGuard.validate_expiration(fresh_prop, ttl_minutes=15)
    assert is_valid_fresh is True
    assert err_fresh is None

    # 2. Expired proposal (> 15 mins)
    expired_prop = ActionProposal(
        proposal_id="prop-expired",
        intent_type=ActionIntentType.CREATE_TASK,
        title="Expired Task",
        created_at=datetime.now(timezone.utc) - timedelta(minutes=20)
    )
    is_valid_exp, err_exp = ActionSafetyGuard.validate_expiration(expired_prop, ttl_minutes=15)
    assert is_valid_exp is False
    assert err_exp is not None and "expired" in err_exp.lower()

    print("[PASS] Test: Proposal expiration validation TTL")

def test_workspace_scope_isolation():
    user = DummyUser()
    user.current_workspace_id = uuid4()

    # 1. Matching workspace
    prop_matching = ActionProposal(
        proposal_id="prop-match",
        intent_type=ActionIntentType.CREATE_TASK,
        title="Task",
        workspace_id=str(user.current_workspace_id)
    )
    is_valid_ws, err_ws = ActionSafetyGuard.validate_workspace_scope(prop_matching, user)
    assert is_valid_ws is True

    # 2. Mismatched workspace
    prop_other = ActionProposal(
        proposal_id="prop-other",
        intent_type=ActionIntentType.CREATE_TASK,
        title="Task",
        workspace_id=str(uuid4())
    )
    is_valid_other, err_other = ActionSafetyGuard.validate_workspace_scope(prop_other, user)
    assert is_valid_other is False
    assert err_other is not None and "mismatch" in err_other.lower()

    print("[PASS] Test: Workspace scope isolation validation")

def test_idempotency_double_click_protection():
    user = DummyUser()
    db = DummyDB()
    proposal_id = f"prop-idemp-{uuid4().hex[:6]}"

    req = ActionConfirmRequest(
        proposal_id=proposal_id,
        intent_type=ActionIntentType.CREATE_REMINDER,
        parameters={"reminder_text": "Review report"},
        confirm=True,
        workspace_id=str(user.current_workspace_id)
    )

    # First execution (adds to _EXECUTED_PROPOSALS)
    _EXECUTED_PROPOSALS.add(proposal_id)

    # Second execution (blocked by idempotency check)
    res_second = asyncio.run(confirm_action_proposal(req, user, db))
    assert res_second.status == ActionResultStatus.SUCCESS
    assert res_second.metadata.get("duplicate_blocked") is True

    print("[PASS] Test: Server-side idempotency double-click protection")

def test_destructive_action_blocking():
    user = DummyUser()
    db = DummyDB()

    req = ActionConfirmRequest(
        proposal_id=f"prop-del-{uuid4().hex[:6]}",
        intent_type=ActionIntentType.DELETE_DOCUMENT,
        parameters={"document_id": str(uuid4())},
        confirm=True,
        workspace_id=str(user.current_workspace_id)
    )

    res_del = asyncio.run(confirm_action_proposal(req, user, db))
    assert res_del.status == ActionResultStatus.FAILED
    assert res_del.error_code == "DESTRUCTIVE_ACTION_BLOCKED"

    print("[PASS] Test: Destructive action protection blocking")

if __name__ == "__main__":
    print("Running AUTO-06 Action Confirmation & Safety Test Suite...")
    test_action_safety_policy_evaluation()
    test_proposal_expiration_validation()
    test_workspace_scope_isolation()
    test_idempotency_double_click_protection()
    test_destructive_action_blocking()
    print("\nALL AUTO-06 EXECUTION TESTS PASSED SUCCESSFULLY!")
