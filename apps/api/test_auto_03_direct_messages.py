import asyncio
import sys
import os
from uuid import uuid4

# Add apps/api to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../apps/api')))

from app.actions.classifier import ActionClassifier
from app.actions.types import ActionIntentType, ActionStatus, ActionResultStatus
from app.actions.executors.direct_message_executor import DirectMessageActionExecutor

def test_direct_message_classification():
    # 1. Message query
    prop = ActionClassifier.classify("Message Dhruvil that the API integration is ready.")
    assert prop is not None
    assert prop.intent_type == ActionIntentType.SEND_DIRECT_MESSAGE
    assert prop.parameters.get("recipient_name") == "Dhruvil"
    assert "API integration is ready" in prop.parameters.get("message_body")
    print("[PASS] Direct Message Classification test ('Message Dhruvil that the API integration is ready.')")

    # 2. Tell query
    prop2 = ActionClassifier.classify("Tell Kaizan the deployment has been completed.")
    assert prop2 is not None
    assert prop2.intent_type == ActionIntentType.SEND_DIRECT_MESSAGE
    assert prop2.parameters.get("recipient_name") == "Kaizan"
    print("[PASS] Direct Message Classification test ('Tell Kaizan...')")

def test_unknown_recipient_handling():
    executor = DirectMessageActionExecutor()

    class DummyUser:
        id = uuid4()
        organization_id = uuid4()
        current_workspace_id = uuid4()
        email = "testuser@mindmesh.com"
        name = "Test User"

    prop = ActionClassifier.classify("Message Rahul that the deployment is ready.")

    # Mock AsyncSession check
    class DummyDB:
        async def execute(self, stmt):
            class DummyResult:
                def scalars(self):
                    class DummyScalars:
                        def all(self): return []
                    return DummyScalars()
            return DummyResult()

    res = asyncio.run(executor.execute(prop, DummyUser(), DummyDB()))
    assert res.status == ActionResultStatus.FAILED
    assert "couldn't find a workspace member" in res.message
    print("[PASS] Unknown Recipient Handling test")

if __name__ == "__main__":
    print("Running AUTO-03 Direct Message Actions Test Suite...")
    test_direct_message_classification()
    test_unknown_recipient_handling()
    print("ALL AUTO-03 BACKEND TESTS PASSED SUCCESSFULLY!")
