import asyncio
import sys
import os

# Add apps/api to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../apps/api')))

from app.actions.classifier import ActionClassifier
from app.actions.types import ActionIntentType, ActionStatus, ActionResultStatus
from app.actions.executors.task_executor import CreateTaskActionExecutor
from app.actions.executors.unimplemented import UnimplementedActionExecutor

def test_question_vs_action_separation():
    # 1. Read-only questions should return None for action proposal
    assert ActionClassifier.classify("What tasks are pending?") is None
    assert ActionClassifier.classify("How many PDFs are in documents?") is None
    assert ActionClassifier.classify("Who owns this project?") is None
    print("[PASS] Question vs Action Separation test")

def test_create_task_classification():
    # 2. Action query should produce ActionProposal
    proposal = ActionClassifier.classify("Create a task to review the project report.")
    assert proposal is not None
    assert proposal.intent_type == ActionIntentType.CREATE_TASK
    assert proposal.parameters.get("title") == "Review the project report"
    assert proposal.status == ActionStatus.READY_FOR_CONFIRMATION
    print("[PASS] Create Task Classification test")

def test_ambiguity_handling():
    # 3. Ambiguous create task request should request clarification
    proposal = ActionClassifier.classify("Create a task.")
    assert proposal is not None
    assert proposal.status == ActionStatus.NEEDS_CLARIFICATION
    assert proposal.clarification_prompt is not None and "task" in proposal.clarification_prompt.lower()
    print("[PASS] Ambiguity Handling test")

def test_unimplemented_action_safety():
    # 4. Unimplemented actions return NOT_IMPLEMENTED status
    proposal = ActionClassifier.classify("Send Dhruvil a message saying deployment is ready.")
    assert proposal is not None
    assert proposal.intent_type == ActionIntentType.SEND_DIRECT_MESSAGE

    executor = UnimplementedActionExecutor()
    # Mock execution check
    class DummyUser:
        email = "testuser@mindmesh.com"

    res = asyncio.run(executor.execute(proposal, DummyUser(), None))
    assert res.status == ActionResultStatus.NOT_IMPLEMENTED
    assert "not available yet" in res.message
    print("[PASS] Unimplemented Action Safety test")

if __name__ == "__main__":
    print("Running AUTO-01 Action Engine Test Suite...")
    test_question_vs_action_separation()
    test_create_task_classification()
    test_ambiguity_handling()
    test_unimplemented_action_safety()
    print("ALL AUTO-01 BACKEND TESTS PASSED SUCCESSFULLY!")
