import sys
import os
from datetime import datetime, timedelta, timezone

# Add apps/api to sys.path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app.proactive.detection_engine import ProactiveDetectionEngine
from app.actions.candidate import IntentCategory, ActionType, ConfidenceLevel, CandidateStatus

def test_1_commitment_with_deadline():
    msg = "I'll finish the deployment report by Friday."
    candidate = ProactiveDetectionEngine.detect_candidate_action(
        text=msg,
        source_type="DIRECT_MESSAGE",
        conversation_id="conv-1",
        sender_name="Priyam"
    )
    assert candidate is not None
    assert candidate.intent == IntentCategory.COMMITMENT
    assert candidate.action_type == ActionType.TASK
    assert "deployment report" in candidate.subject.lower()
    assert candidate.deadline == "Friday"
    assert candidate.confidence_level == ConfidenceLevel.HIGH
    assert candidate.confidence >= 0.85
    assert candidate.assignee_name == "Priyam"
    print("[PASS] Test 1: Commitment with deadline")

def test_2_request_with_relative_meeting_deadline():
    msg = "Please send the final PPT before tomorrow's client meeting."
    candidate = ProactiveDetectionEngine.detect_candidate_action(
        text=msg,
        source_type="DIRECT_MESSAGE",
        conversation_id="conv-2",
        sender_name="Rahul"
    )
    assert candidate is not None
    assert candidate.intent in (IntentCategory.TASK_REQUEST, IntentCategory.REQUEST_TO_PERSON)
    assert candidate.action_type == ActionType.TASK
    assert "Send the final ppt" in candidate.subject
    assert candidate.deadline == "Before tomorrow's client meeting"
    assert candidate.normalized_deadline is not None
    assert candidate.confidence_level == ConfidenceLevel.HIGH
    print("[PASS] Test 2: Request with relative meeting deadline")

def test_3_commitment_without_invented_deadline():
    msg = "I'll review the README and send feedback."
    candidate = ProactiveDetectionEngine.detect_candidate_action(
        text=msg,
        source_type="DIRECT_MESSAGE",
        conversation_id="conv-3",
        sender_name="Priyam"
    )
    assert candidate is not None
    assert candidate.intent == IntentCategory.COMMITMENT
    assert candidate.action_type == ActionType.TASK
    assert "Review the readme" in candidate.subject or "send feedback" in candidate.subject.lower()
    assert candidate.deadline is None
    assert candidate.normalized_deadline is None
    print("[PASS] Test 3: Commitment without invented deadline")

def test_4_non_action_date_statement():
    msg = "Our client meeting is Friday."
    candidate = ProactiveDetectionEngine.detect_candidate_action(
        text=msg,
        source_type="DIRECT_MESSAGE",
        conversation_id="conv-4",
        sender_name="Rahul"
    )
    assert candidate is not None
    assert candidate.intent == IntentCategory.INFORMATION_ONLY or candidate.confidence_level == ConfidenceLevel.LOW
    assert candidate.action_type == ActionType.NO_ACTION or candidate.confidence < 0.60
    print("[PASS] Test 4: Non-action date statement")

def test_5_past_tense_completed_statement():
    msg = "The report was completed last Friday."
    candidate = ProactiveDetectionEngine.detect_candidate_action(
        text=msg,
        source_type="DIRECT_MESSAGE",
        conversation_id="conv-5",
        sender_name="Rahul"
    )
    assert candidate is not None
    assert candidate.intent in (IntentCategory.INFORMATION_ONLY, IntentCategory.NO_ACTION)
    assert candidate.confidence_level == ConfidenceLevel.LOW
    print("[PASS] Test 5: Past tense completed statement")

def test_6_group_conversation_context():
    history = [
        {"sender": "Rahul", "content": "Priyam, update the API documentation."}
    ]
    msg = "Sure, I'll do it by Monday."
    candidate = ProactiveDetectionEngine.detect_candidate_action(
        text=msg,
        history=history,
        source_type="GROUP_CONVERSATION",
        conversation_id="conv-group-1",
        sender_name="Priyam"
    )
    assert candidate is not None
    assert candidate.intent == IntentCategory.COMMITMENT
    assert candidate.action_type == ActionType.TASK
    assert "Update the api documentation" in candidate.subject
    assert candidate.assignee_name == "Priyam"
    assert candidate.deadline == "Monday"
    print("[PASS] Test 6: Group conversation context")

def test_7_pronoun_resolution_multi_message():
    history = [
        {"sender": "Rahul", "content": "We need to finish deployment."}
    ]
    msg = "Let's have it ready by Friday."
    candidate = ProactiveDetectionEngine.detect_candidate_action(
        text=msg,
        history=history,
        source_type="PROJECT",
        conversation_id="conv-proj-1",
        sender_name="Rahul"
    )
    assert candidate is not None
    assert "Finish deployment" in candidate.subject
    assert candidate.deadline == "Friday"
    print("[PASS] Test 7: Pronoun resolution multi-message")

def test_8_low_confidence_speculative_statement():
    msg = "I'm not sure, maybe next week."
    candidate = ProactiveDetectionEngine.detect_candidate_action(
        text=msg,
        source_type="DIRECT_MESSAGE",
        conversation_id="conv-8",
        sender_name="Priyam"
    )
    assert candidate is not None
    assert candidate.confidence_level == ConfidenceLevel.LOW
    assert candidate.confidence < 0.60
    print("[PASS] Test 8: Low confidence speculative statement")

def test_9_topic_change_cutoff():
    history = [
        {"sender": "Rahul", "content": "We need to finish deployment."},
        {"sender": "Priyam", "content": "By Friday."},
        {"sender": "Rahul", "content": "Anyway, how was your weekend?"}
    ]
    msg = "It was great, thanks!"
    candidate = ProactiveDetectionEngine.detect_candidate_action(
        text=msg,
        history=history,
        source_type="DIRECT_MESSAGE",
        conversation_id="conv-9",
        sender_name="Priyam"
    )
    assert candidate is not None
    assert candidate.intent == IntentCategory.NO_ACTION or candidate.confidence_level == ConfidenceLevel.LOW
    print("[PASS] Test 9: Topic change cutoff")

def test_10_unseen_natural_language_variants():
    variants = [
        ("I've got to get the deployment docs finished before Friday.", "Friday"),
        ("I should probably send the final deck tomorrow.", "tomorrow"),
        ("Can someone make sure testing is done before the demo?", "Before the demo"),
        ("I'll take care of the API docs this week.", "this week"),
        ("Don't let me forget about the deployment report.", None)
    ]
    for text, expected_deadline in variants:
        candidate = ProactiveDetectionEngine.detect_candidate_action(
            text=text,
            source_type="DIRECT_MESSAGE",
            conversation_id="conv-var",
            sender_name="Tester"
        )
        print(f"DEBUG text='{text}' -> intent={candidate.intent}, subject='{candidate.subject}', deadline='{candidate.deadline}', conf={candidate.confidence_level}")
        assert candidate is not None
        assert candidate.confidence_level in (ConfidenceLevel.HIGH, ConfidenceLevel.MEDIUM)
        assert candidate.subject is not None
        if expected_deadline:
            assert candidate.deadline is not None
    print("[PASS] Test 10: Unseen natural language variants")

def test_11_candidate_provenance_and_hash():
    msg = "I'll submit the weekly status report by EOD."
    candidate = ProactiveDetectionEngine.detect_candidate_action(
        text=msg,
        source_type="DIRECT_MESSAGE",
        conversation_id="conv-prov-1",
        message_id="msg-123",
        sender_id="usr-456",
        sender_name="Priyam",
        workspace_id="ws-789"
    )
    assert candidate is not None
    assert candidate.source.source_type == "DIRECT_MESSAGE"
    assert candidate.source.conversation_id == "conv-prov-1"
    assert candidate.source.message_id == "msg-123"
    assert candidate.source.sender_id == "usr-456"
    assert candidate.source.workspace_id == "ws-789"
    assert candidate.detected_action_hash != ""
    assert candidate.status == CandidateStatus.DETECTED
    print("[PASS] Test 11: Candidate provenance and hash")

if __name__ == "__main__":
    print("Running AUTO-01 Action & Intent Foundation Test Suite...")
    test_1_commitment_with_deadline()
    test_2_request_with_relative_meeting_deadline()
    test_3_commitment_without_invented_deadline()
    test_4_non_action_date_statement()
    test_5_past_tense_completed_statement()
    test_6_group_conversation_context()
    test_7_pronoun_resolution_multi_message()
    test_8_low_confidence_speculative_statement()
    test_9_topic_change_cutoff()
    test_10_unseen_natural_language_variants()
    test_11_candidate_provenance_and_hash()
    print("\nALL AUTO-01 FOUNDATION TESTS PASSED SUCCESSFULLY!")
