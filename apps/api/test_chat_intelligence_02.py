import sys
import os

# Add apps/api to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../apps/api')))

from app.actions.types import ActionIntentType, ActionStatus
from app.actions.classifier import ActionClassifier
from app.ai.intent.engine import IntentEngine

def test_create_task_paraphrases():
    print("Testing CREATE_TASK Paraphrases...")
    task_queries_with_title = [
        "Create a task to review the report.",
        "Can you add review the report to my task list?",
        "Put reviewing the report on my tasks.",
        "I have to review the report tomorrow, add that as a task.",
        "Add reviewing the project report to my tasks.",
        "Make a task for reviewing the report."
    ]
    for q in task_queries_with_title:
        prop = ActionClassifier.classify(q)
        assert prop is not None, f"Failed to classify: {q}"
        assert prop.intent_type == ActionIntentType.CREATE_TASK, f"Wrong intent for: {q}"
        assert prop.status == ActionStatus.READY_FOR_CONFIRMATION, f"Expected READY_FOR_CONFIRMATION for: {q}, got {prop.status}"
        assert prop.parameters.get("title") is not None, f"Missing title for: {q}"
        print(f"  [PASS] '{q}' -> Title: '{prop.parameters.get('title')}'")

def test_create_task_clarifications():
    print("Testing CREATE_TASK Missing Parameter Clarifications...")
    task_queries_missing_title = [
        "Create a task.",
        "Add something to my tasks.",
        "Can you put something on my todo list?",
        "I need to add a task.",
        "Make me a task.",
        "Can you create something I need to do?"
    ]
    for q in task_queries_missing_title:
        prop = ActionClassifier.classify(q)
        assert prop is not None, f"Failed to classify: {q}"
        assert prop.intent_type == ActionIntentType.CREATE_TASK, f"Wrong intent for: {q}"
        assert prop.status == ActionStatus.NEEDS_CLARIFICATION, f"Expected NEEDS_CLARIFICATION for: {q}, got {prop.status}"
        assert "What should the task be about?" in prop.clarification_prompt
        print(f"  [PASS] '{q}' -> Clarification: '{prop.clarification_prompt}'")

def test_structural_math_vs_ambiguous():
    print("Testing Structural Math vs. Concept vs. Ambiguous Addition...")
    
    # 1. Ambiguous addition ("what addition?") - MUST NOT BE 2+2=4!
    res_ambig = IntentEngine.understand_query("what addition?")
    assert res_ambig.intent.value == "AMBIGUOUS", f"Expected AMBIGUOUS for 'what addition?', got {res_ambig.intent.value}"
    print("  [PASS] 'what addition?' -> AMBIGUOUS (Clarification route)")

    # 2. Structural Math Calculation ("What is 25 + 17?")
    res_math1 = IntentEngine.understand_query("What is 25 + 17?")
    assert res_math1.intent.value == "GENERAL_KNOWLEDGE"
    print("  [PASS] 'What is 25 + 17?' -> GENERAL_KNOWLEDGE (Math)")

    # 3. Word Math Calculation ("What is 2 plus 2?")
    res_math2 = IntentEngine.understand_query("What is 2 plus 2?")
    assert res_math2.intent.value == "GENERAL_KNOWLEDGE"
    print("  [PASS] 'What is 2 plus 2?' -> GENERAL_KNOWLEDGE (Math)")

    # 4. Concept Explanation ("Explain addition")
    res_concept = IntentEngine.understand_query("Explain addition")
    assert res_concept.intent.value == "GENERAL_KNOWLEDGE"
    print("  [PASS] 'Explain addition' -> GENERAL_KNOWLEDGE (Concept)")

def test_reminder_paraphrases():
    print("Testing REMINDER Paraphrases...")
    rem_queries = [
        ("Remind me tomorrow to submit the report.", ActionStatus.READY_FOR_CONFIRMATION),
        ("Don't let me forget the report tomorrow.", ActionStatus.READY_FOR_CONFIRMATION),
        ("Set a reminder for tomorrow.", ActionStatus.NEEDS_CLARIFICATION),
        ("Can you remind me about the report?", ActionStatus.READY_FOR_CONFIRMATION)
    ]
    for q, expected_status in rem_queries:
        prop = ActionClassifier.classify(q)
        assert prop is not None, f"Failed to classify: {q}"
        assert prop.intent_type == ActionIntentType.CREATE_REMINDER, f"Wrong intent for: {q}"
        assert prop.status == expected_status, f"Expected {expected_status} for '{q}', got {prop.status}"
        print(f"  [PASS] '{q}' -> Status: {prop.status}")

def test_direct_message_paraphrases():
    print("Testing DIRECT_MESSAGE Paraphrases...")
    dm_queries = [
        ("Tell Dhruvil the API is ready.", ActionStatus.READY_FOR_CONFIRMATION),
        ("Message Dhruvil that the API is ready.", ActionStatus.READY_FOR_CONFIRMATION),
        ("Send Dhruvil a DM.", ActionStatus.NEEDS_CLARIFICATION),
        ("Send a message", ActionStatus.NEEDS_CLARIFICATION)
    ]
    for q, expected_status in dm_queries:
        prop = ActionClassifier.classify(q)
        assert prop is not None, f"Failed to classify: {q}"
        assert prop.intent_type == ActionIntentType.SEND_DIRECT_MESSAGE, f"Wrong intent for: {q}"
        assert prop.status == expected_status, f"Expected {expected_status} for '{q}', got {prop.status}"
        print(f"  [PASS] '{q}' -> Status: {prop.status}")

if __name__ == "__main__":
    print("==========================================================")
    print("RUNNING CHAT-INTELLIGENCE-02 ADVERSARIAL SUITE")
    print("==========================================================")
    test_create_task_paraphrases()
    test_create_task_clarifications()
    test_structural_math_vs_ambiguous()
    test_reminder_paraphrases()
    test_direct_message_paraphrases()
    print("==========================================================")
    print("ALL CHAT-INTELLIGENCE-02 BACKEND SUITE PASSED SUCCESSFULLY!")
    print("==========================================================")
