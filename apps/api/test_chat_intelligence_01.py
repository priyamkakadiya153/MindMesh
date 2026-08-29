import asyncio
import sys
import os
from uuid import uuid4

# Add apps/api to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../apps/api')))

from app.actions.types import ActionIntentType, ActionStatus
from app.actions.classifier import ActionClassifier
from app.ai.intent.engine import IntentEngine

def test_incomplete_action_clarification():
    # 1. "create a task" -> NEEDS_CLARIFICATION
    prop = ActionClassifier.classify("create a task")
    assert prop is not None
    assert prop.intent_type == ActionIntentType.CREATE_TASK
    assert prop.status == ActionStatus.NEEDS_CLARIFICATION
    assert prop.clarification_prompt is not None
    print("[PASS] Incomplete action clarification test ('create a task')")

def test_task_query_classification():
    # 2. "what tasks do I have?" -> is_task_query
    prop = ActionClassifier.classify("what tasks do I have?")
    assert prop is not None
    assert prop.intent_type == ActionIntentType.CREATE_TASK
    assert prop.parameters.get("is_task_query") is True
    print("[PASS] Task query classification test ('what tasks do I have?')")

def test_general_knowledge_math_classification():
    # 3. "what is 2 + 2?" -> GENERAL_KNOWLEDGE
    res_math = IntentEngine.understand_query("what is 2 + 2?")
    assert res_math.intent.value == "GENERAL_KNOWLEDGE"
    assert res_math.requires_retrieval is False

    # 4. "what is 25 * 4?" -> GENERAL_KNOWLEDGE
    res_math2 = IntentEngine.understand_query("what is 25 * 4?")
    assert res_math2.intent.value == "GENERAL_KNOWLEDGE"
    assert res_math2.requires_retrieval is False

    # 5. "hello" -> GREETING
    res_hello = IntentEngine.understand_query("hello")
    assert res_hello.intent.value == "GREETING"
    assert res_hello.requires_retrieval is False

    print("[PASS] Math & Greeting fast-path classification tests ('what is 2 + 2?', 'hello')")

if __name__ == "__main__":
    print("Running CHAT-INTELLIGENCE-01 Test Suite...")
    test_incomplete_action_clarification()
    test_task_query_classification()
    test_general_knowledge_math_classification()
    print("ALL CHAT-INTELLIGENCE-01 BACKEND TESTS PASSED SUCCESSFULLY!")
