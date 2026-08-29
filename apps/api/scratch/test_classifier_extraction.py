import sys
import os

sys.path.insert(0, os.path.abspath("."))

from app.actions.classifier import ActionClassifier
from app.actions.types import ActionStatus

def run_tests():
    print("--- Running Action Classifier Parameter Extraction Tests ---")

    # TEST 1
    q1 = "Create a task to review the deployment report tomorrow."
    p1 = ActionClassifier.classify(q1)
    print(f"[TEST 1]: '{q1}'")
    print(f"  Title: '{p1.parameters.get('title')}'")
    print(f"  Due: '{p1.parameters.get('due_date_str')}'")
    assert p1.parameters.get('title') == "Review the deployment report", f"Expected 'Review the deployment report', got '{p1.parameters.get('title')}'"
    assert p1.parameters.get('due_date_str') == "tomorrow", f"Expected 'tomorrow', got '{p1.parameters.get('due_date_str')}'"
    print("  PASS 1\n")

    # TEST 2
    q2 = "Can you put reviewing the deployment report on my todo list?"
    p2 = ActionClassifier.classify(q2)
    print(f"[TEST 2]: '{q2}'")
    print(f"  Title: '{p2.parameters.get('title')}'")
    print(f"  Due: '{p2.parameters.get('due_date_str')}'")
    assert p2.parameters.get('title') == "Reviewing the deployment report", f"Expected 'Reviewing the deployment report', got '{p2.parameters.get('title')}'"
    assert p2.parameters.get('due_date_str') is None, f"Expected None, got '{p2.parameters.get('due_date_str')}'"
    print("  PASS 2\n")

    # TEST 3
    q3 = "Create a task."
    p3 = ActionClassifier.classify(q3)
    print(f"[TEST 3]: '{q3}'")
    print(f"  Status: {p3.status}")
    print(f"  Prompt: '{p3.clarification_prompt}'")
    assert p3.status == ActionStatus.NEEDS_CLARIFICATION
    print("  PASS 3\n")

    # TEST 4 (Antecedent Pronoun Resolution)
    q4 = "Can you put that on my list?"
    context4 = {"followup_goal": {"title": "Review the deployment report", "due_date_str": "tomorrow"}}
    p4 = ActionClassifier.classify(q4, resolved_context=context4)
    print(f"[TEST 4]: '{q4}' with context")
    print(f"  Title: '{p4.parameters.get('title')}'")
    print(f"  Due: '{p4.parameters.get('due_date_str')}'")
    assert p4.parameters.get('title') == "Review the deployment report"
    assert p4.parameters.get('due_date_str') == "tomorrow"
    print("  PASS 4\n")

    print("==========================================================================")
    print("ALL CLASSIFIER PARAMETER EXTRACTION TESTS PASSED 100%!")
    print("==========================================================================")

if __name__ == "__main__":
    run_tests()
