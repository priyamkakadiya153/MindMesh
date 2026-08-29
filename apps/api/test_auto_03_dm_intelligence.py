import asyncio
import sys
import os
from uuid import uuid4
from datetime import datetime, timezone

# Add apps/api to path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app.actions.executors.direct_message_executor import DirectMessageActionExecutor
from app.actions.classifier import ActionClassifier
from app.actions.registry import action_registry
from app.actions.types import ActionProposal, ActionIntentType, ActionStatus, ActionResultStatus

def test_natural_language_dm_variants():
    queries = [
        ("Message Rahul that the deployment is ready.", "Rahul", "The deployment is ready"),
        ("Tell Dhruvil the API integration is complete.", "Dhruvil", "The API integration is complete"),
        ("Let Rahul know that testing has started.", "Rahul", "Testing has started"),
        ("Send a DM to Dhruvil: the frontend is complete.", "Dhruvil", "The frontend is complete"),
        ("Tell Rahul I'll send the report tomorrow.", "Rahul", "I'll send the report tomorrow"),
        ("Can you inform Dhruvil that the meeting moved to Monday?", "Dhruvil", "The meeting moved to Monday"),
        ("Tell the team that the backend API is ready.", "the team", "The backend API is ready"),
    ]

    for q, expected_rec, expected_content_sub in queries:
        prop = ActionClassifier.classify(q)
        assert prop is not None, f"Failed classifying query: '{q}'"
        assert prop.intent_type == ActionIntentType.SEND_DIRECT_MESSAGE, f"Wrong intent for '{q}'"
        rec = prop.parameters.get("recipient_name", "")
        assert expected_rec.lower() in rec.lower(), f"Expected recipient '{expected_rec}' in '{rec}' for '{q}'"
        body = prop.parameters.get("message_body", "")
        assert expected_content_sub.lower() in body.lower(), f"Expected content '{expected_content_sub}' in '{body}' for '{q}'"

    print("[PASS] Test: Natural Language DM variants & clean content extraction")

def test_pronoun_and_context_resolution():
    resolved_context = {"last_speaker": "Rahul", "last_mentioned_user": "Dhruvil"}
    prop = ActionClassifier.classify("Tell him it's ready.", resolved_context=resolved_context)
    assert prop is not None
    assert prop.intent_type == ActionIntentType.SEND_DIRECT_MESSAGE
    assert prop.parameters.get("recipient_name") == "Dhruvil"
    assert "ready" in prop.parameters.get("message_body", "").lower()
    print("[PASS] Test: Pronoun & context resolution ('him' -> Dhruvil)")

def test_missing_recipient_clarification():
    prop = ActionClassifier.classify("Send a message.")
    assert prop is not None
    assert prop.status == ActionStatus.NEEDS_CLARIFICATION
    assert prop.clarification_prompt is not None and "who" in prop.clarification_prompt.lower()
    print("[PASS] Test: Missing recipient clarification prompt")

def test_missing_message_body_clarification():
    prop = ActionClassifier.classify("Message Rahul.")
    assert prop is not None
    assert prop.status == ActionStatus.NEEDS_CLARIFICATION
    assert prop.clarification_prompt is not None and "what" in prop.clarification_prompt.lower()
    print("[PASS] Test: Missing message body clarification prompt")

def test_read_only_conversation_queries():
    read_only_queries = [
        "What did Rahul say about the deployment?",
        "When did Dhruvil tell me the API was ready?",
        "Summarize my conversation with Rahul.",
        "What did the team decide about the release?"
    ]

    for q in read_only_queries:
        prop = ActionClassifier.classify(q)
        assert prop is None, f"Query '{q}' should be read-only and return None"

    print("[PASS] Test: Read-only conversation questions separation")

def test_direct_message_execution_flow():
    class DummyUser:
        id = uuid4()
        organization_id = uuid4()
        current_workspace_id = uuid4()
        email = "sender@mindmesh.com"
        full_name = "Priyam Sender"

    class DummyRecipient:
        id = uuid4()
        email = "rahul@mindmesh.com"
        full_name = "Rahul Member"

    class DummyConv:
        id = uuid4()
        organization_id = DummyUser.organization_id
        type = "private"

    class DummyDM:
        id = uuid4()
        created_at = datetime.now(timezone.utc)

    class DummyDB:
        def __init__(self):
            self.added = []

        async def execute(self, stmt):
            items = self.added
            class Res:
                def scalar_one_or_none(self):
                    # For user search, return DummyRecipient
                    if getattr(self, "_is_user_query", False):
                        return DummyRecipient()
                    return DummyDM()
                def scalars(self):
                    class SubRes:
                        def first(self):
                            return DummyConv()
                        def all(self):
                            return [DummyRecipient()]
                    return SubRes()
            r = Res()
            return r

        def add(self, obj):
            if not getattr(obj, "id", None):
                obj.id = uuid4()
            self.added.append(obj)

        def add_all(self, objs):
            for o in objs:
                self.add(o)

        async def flush(self):
            pass
        async def commit(self):
            pass
        async def refresh(self, obj):
            pass
        async def rollback(self):
            pass

    executor = DirectMessageActionExecutor()
    proposal = ActionProposal(
        proposal_id=f"prop-dm-{uuid4().hex[:6]}",
        intent_type=ActionIntentType.SEND_DIRECT_MESSAGE,
        title="Send Message to Rahul",
        parameters={"recipient_name": "Rahul", "message_body": "The deployment is ready."},
        workspace_id=str(DummyUser.current_workspace_id),
        user_id=str(DummyUser.id),
        confirmation_required=True,
        status=ActionStatus.CONFIRMED
    )

    db = DummyDB()
    result = asyncio.run(executor.execute(proposal, DummyUser(), db))
    assert result.status == ActionResultStatus.SUCCESS
    assert "Rahul" in result.entity_name
    print("[PASS] Test: DirectMessageActionExecutor real execution & DB persistence verification")

if __name__ == "__main__":
    print("Running AUTO-03 Direct Messages Test Suite...")
    test_natural_language_dm_variants()
    test_pronoun_and_context_resolution()
    test_missing_recipient_clarification()
    test_missing_message_body_clarification()
    test_read_only_conversation_queries()
    test_direct_message_execution_flow()
    print("\nALL AUTO-03 EXECUTION TESTS PASSED SUCCESSFULLY!")
