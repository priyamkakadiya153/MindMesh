import asyncio
import sys
import os
from uuid import uuid4

# Add apps/api to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../apps/api')))

from app.actions.types import ActionIntentType
from app.actions.classifier import ActionClassifier
from app.ai.chat.session import ChatSessionManager

def test_typo_action_classification():
    # 1. "creat a task" typo match
    p_creat = ActionClassifier.classify("creat a task to review system architecture")
    assert p_creat is not None
    assert p_creat.intent_type == ActionIntentType.CREATE_TASK
    assert "Review system architecture" in p_creat.title

    # 2. "creat task" typo match
    p_creat_short = ActionClassifier.classify("creat task")
    assert p_creat_short is not None
    assert p_creat_short.intent_type == ActionIntentType.CREATE_TASK

    # 3. "creat a reminder" typo match
    p_rem = ActionClassifier.classify("creat a reminder to submit status")
    assert p_rem is not None
    assert p_rem.intent_type == ActionIntentType.CREATE_REMINDER

    print("[PASS] ActionClassifier typo matching (creat a task / creat task) test")

if __name__ == "__main__":
    print("Running CHAT-FIX-02 Test Suite...")
    test_typo_action_classification()
    print("ALL CHAT-FIX-02 BACKEND TESTS PASSED SUCCESSFULLY!")
