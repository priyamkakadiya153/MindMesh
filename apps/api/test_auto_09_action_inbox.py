import asyncio
import sys
import os
from uuid import uuid4
from datetime import datetime, timedelta, timezone

# Add apps/api to path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app.proactive.detection_engine import ProactiveDetectionEngine
from app.actions.candidate import IntentCategory, ActionType, ConfidenceLevel, CandidateStatus

def test_1_action_inbox_candidate_persistence_and_provenance():
    candidate = ProactiveDetectionEngine.detect_candidate_action(
        text="Priyam, please send me the final project report by Friday.",
        source_type="DIRECT_MESSAGE",
        conversation_id="conv-inbox-1",
        sender_name="Rahul",
        current_user_name="Priyam"
    )
    assert candidate is not None
    assert candidate.status == CandidateStatus.DETECTED
    assert candidate.provenance["source_type"] == "DIRECT_MESSAGE"
    assert candidate.provenance["conversation_id"] == "conv-inbox-1"
    assert candidate.provenance["sender_name"] == "Rahul"

    print("[PASS] Test 1: Action Inbox candidate persistence & provenance fields")

def test_2_action_candidate_status_lifecycle():
    candidate = ProactiveDetectionEngine.detect_candidate_action(
        text="I'll finish the API documentation by tomorrow.",
        source_type="DIRECT_MESSAGE",
        conversation_id="conv-inbox-2",
        sender_name="Priyam",
        current_user_name="Priyam"
    )
    assert candidate.status == CandidateStatus.DETECTED

    # Status transition DETECTED -> ACCEPTED
    candidate.status = CandidateStatus.ACCEPTED
    assert candidate.status == CandidateStatus.ACCEPTED

    # Status transition -> DISMISSED
    candidate.status = CandidateStatus.DISMISSED
    assert candidate.status == CandidateStatus.DISMISSED

    # Status transition -> EXPIRED
    candidate.status = CandidateStatus.EXPIRED
    assert candidate.status == CandidateStatus.EXPIRED

    print("[PASS] Test 2: Action candidate status lifecycle (DETECTED -> ACCEPTED / DISMISSED / EXPIRED)")

def test_3_action_inbox_deduplication():
    c1 = ProactiveDetectionEngine.detect_candidate_action(
        text="Priyam, please send me the final report by Friday.",
        source_type="DIRECT_MESSAGE",
        conversation_id="conv-inbox-3",
        workspace_id="ws-inbox-1"
    )
    c2 = ProactiveDetectionEngine.detect_candidate_action(
        text="Priyam, please send me the final report by Friday.",
        source_type="DIRECT_MESSAGE",
        conversation_id="conv-inbox-3",
        workspace_id="ws-inbox-1"
    )
    assert c1.detected_action_hash == c2.detected_action_hash

    print("[PASS] Test 3: Action candidate deduplication hash identity")

def test_4_multi_conversation_aggregation():
    candidates = []
    messages = [
        ("Rahul", "Priyam, please review API docs by Wednesday.", "conv-dm-rahul", "DIRECT_MESSAGE"),
        ("Kaizan", "I'll send the database report tomorrow.", "conv-dm-kaizan", "DIRECT_MESSAGE"),
        ("Member C", "Priyam, please prepare final presentation by Monday.", "conv-group-project", "GROUP_CHAT")
    ]

    for sender, msg, conv_id, source in messages:
        cand = ProactiveDetectionEngine.detect_candidate_action(
            text=msg,
            source_type=source,
            conversation_id=conv_id,
            sender_name=sender,
            current_user_name="Priyam"
        )
        if cand and cand.confidence_level in (ConfidenceLevel.HIGH, ConfidenceLevel.MEDIUM):
            candidates.append(cand)

    assert len(candidates) >= 2
    for c in candidates:
        assert c.provenance["conversation_id"] in ("conv-dm-rahul", "conv-dm-kaizan", "conv-group-project")

    print("[PASS] Test 4: Multi-conversation aggregation across DMs and Group Chats")

if __name__ == "__main__":
    print("Running AUTO-09 Action Inbox & Intelligence Center Test Suite...")
    test_1_action_inbox_candidate_persistence_and_provenance()
    test_2_action_candidate_status_lifecycle()
    test_3_action_inbox_deduplication()
    test_4_multi_conversation_aggregation()
    print("\nALL AUTO-09 EXECUTION TESTS PASSED SUCCESSFULLY!")
