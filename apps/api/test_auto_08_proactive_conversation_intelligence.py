import asyncio
import sys
import os
from uuid import uuid4
from datetime import datetime, timedelta, timezone

# Add apps/api to path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app.proactive.detection_engine import ProactiveDetectionEngine
from app.actions.candidate import IntentCategory, ActionType, ConfidenceLevel, CandidateStatus

def test_1_explicit_request_with_deadline():
    candidate = ProactiveDetectionEngine.detect_candidate_action(
        text="Priyam, please send me the final deployment report by Friday.",
        source_type="DIRECT_MESSAGE",
        conversation_id="conv-dm-1",
        sender_name="Rahul",
        current_user_name="Priyam"
    )
    assert candidate is not None
    assert candidate.intent == IntentCategory.TASK_REQUEST or candidate.intent == IntentCategory.REQUEST_TO_PERSON
    assert candidate.confidence_level == ConfidenceLevel.HIGH
    assert candidate.personal_relevance == ConfidenceLevel.HIGH
    assert candidate.deadline is not None and "friday" in candidate.deadline.lower()
    assert candidate.subject is not None and "deployment report" in candidate.subject.lower()

    print("[PASS] Test 1: Explicit request with deadline directed to current user")

def test_2_self_commitment_with_deadline():
    candidate = ProactiveDetectionEngine.detect_candidate_action(
        text="I'll finish the API documentation by tomorrow morning.",
        source_type="DIRECT_MESSAGE",
        conversation_id="conv-dm-2",
        sender_name="Priyam",
        current_user_name="Priyam"
    )
    assert candidate is not None
    assert candidate.intent == IntentCategory.COMMITMENT
    assert candidate.confidence_level == ConfidenceLevel.HIGH
    assert candidate.personal_relevance == ConfidenceLevel.HIGH
    assert candidate.deadline is not None and "tomorrow" in candidate.deadline.lower()

    print("[PASS] Test 2: Self-commitment with deadline")

def test_3_third_person_group_attribution_low_relevance():
    candidate = ProactiveDetectionEngine.detect_candidate_action(
        text="Kaizan will update the API docs by Friday.",
        source_type="GROUP_CHAT",
        conversation_id="conv-group-1",
        sender_name="Rahul",
        current_user_name="Priyam" # Current user is Priyam, not Kaizan
    )
    assert candidate is not None
    assert candidate.assignee_name == "Kaizan"
    assert candidate.personal_relevance == ConfidenceLevel.LOW

    print("[PASS] Test 3: Third-person group attribution has LOW personal relevance for other members")

def test_4_non_actionable_date_statement_filtered():
    candidate = ProactiveDetectionEngine.detect_candidate_action(
        text="The client meeting is Friday.",
        source_type="DIRECT_MESSAGE",
        conversation_id="conv-dm-3",
        sender_name="Rahul",
        current_user_name="Priyam"
    )
    assert candidate is not None
    assert candidate.intent in (IntentCategory.INFORMATION_ONLY, IntentCategory.NO_ACTION)
    assert candidate.confidence_level == ConfidenceLevel.LOW
    assert candidate.action_type == ActionType.NO_ACTION

    print("[PASS] Test 4: Non-actionable date statement filtered out")

def test_5_historical_completed_statement_filtered():
    candidate = ProactiveDetectionEngine.detect_candidate_action(
        text="I finished the deployment report yesterday.",
        source_type="DIRECT_MESSAGE",
        conversation_id="conv-dm-4",
        sender_name="Rahul",
        current_user_name="Rahul"
    )
    assert candidate is not None
    assert candidate.intent in (IntentCategory.INFORMATION_ONLY, IntentCategory.NO_ACTION, IntentCategory.COMPLETION_SIGNAL)
    assert candidate.confidence_level == ConfidenceLevel.LOW
    assert candidate.action_type in (ActionType.NO_ACTION, ActionType.COMPLETION)

    print("[PASS] Test 5: Historical completed statement filtered out")

def test_6_pronoun_resolution_multi_message_context():
    history = [
        {"content": "Priyam, please review the deployment report."}
    ]
    candidate = ProactiveDetectionEngine.detect_candidate_action(
        text="Can you finish it by Friday?",
        history=history,
        source_type="DIRECT_MESSAGE",
        conversation_id="conv-dm-5",
        sender_name="Rahul",
        current_user_name="Priyam"
    )
    assert candidate is not None
    assert candidate.confidence_level == ConfidenceLevel.HIGH
    assert candidate.deadline is not None and "friday" in candidate.deadline.lower()
    assert candidate.subject is not None and "deployment report" in candidate.subject.lower()

    print("[PASS] Test 6: Pronoun resolution ('it') across multi-message context")

def test_7_topic_change_cutoff_in_history():
    history = [
        {"content": "Priyam, please review the deployment report."},
        {"content": "Anyway, did you see the client email about office lunch?"}
    ]
    candidate = ProactiveDetectionEngine.detect_candidate_action(
        text="That was great.",
        history=history,
        source_type="DIRECT_MESSAGE",
        conversation_id="conv-dm-6",
        sender_name="Rahul",
        current_user_name="Priyam"
    )
    # Topic changed at "Anyway..."; should not resolve "That" back to the deployment report
    assert candidate.intent in (IntentCategory.NO_ACTION, IntentCategory.INFORMATION_ONLY)

    print("[PASS] Test 7: Topic change cutoff prevents carrying stale context across topic shifts")

def test_8_action_hash_deduplication():
    c1 = ProactiveDetectionEngine.detect_candidate_action(
        text="Priyam, please send the report by Friday.",
        source_type="DIRECT_MESSAGE",
        conversation_id="conv-dm-7",
        workspace_id="ws-1"
    )
    c2 = ProactiveDetectionEngine.detect_candidate_action(
        text="Priyam, please send the report by Friday.",
        source_type="DIRECT_MESSAGE",
        conversation_id="conv-dm-7",
        workspace_id="ws-1"
    )
    assert c1.detected_action_hash == c2.detected_action_hash

    print("[PASS] Test 8: Action candidate hash deduplication identity")

if __name__ == "__main__":
    print("Running AUTO-08 Proactive Conversation Intelligence Test Suite...")
    test_1_explicit_request_with_deadline()
    test_2_self_commitment_with_deadline()
    test_3_third_person_group_attribution_low_relevance()
    test_4_non_actionable_date_statement_filtered()
    test_5_historical_completed_statement_filtered()
    test_6_pronoun_resolution_multi_message_context()
    test_7_topic_change_cutoff_in_history()
    test_8_action_hash_deduplication()
    print("\nALL AUTO-08 EXECUTION TESTS PASSED SUCCESSFULLY!")
