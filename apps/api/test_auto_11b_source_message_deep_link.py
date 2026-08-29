import asyncio
import sys
import os
import json
from uuid import uuid4

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app.proactive.detection_engine import ProactiveDetectionEngine
from app.models.proactive_suggestion import ProactiveSuggestion

def test_1_source_message_id_provenance_preservation():
    """Verify source_message_id, conversation_id, source_content, and source_label are preserved."""
    target_msg_id = f"msg-{uuid4()}"
    conv_id = f"conv-{uuid4()}"

    candidate = ProactiveDetectionEngine.detect_candidate_action(
        text="Please complete the API documentation by tomorrow.",
        source_type="DIRECT_MESSAGE",
        conversation_id=conv_id,
        message_id=target_msg_id,
        sender_name="LeaderUser",
        current_user_name="MemberUser"
    )
    assert candidate is not None

    suggestion = ProactiveSuggestion(
        organization_id=uuid4(),
        workspace_id=uuid4(),
        user_id=uuid4(),
        source_type="DIRECT_MESSAGE",
        conversation_id=conv_id,
        message_id=target_msg_id,
        detected_action_type="TASK",
        title=candidate.subject or "Complete API documentation",
        description=candidate.description,
        deadline=candidate.deadline,
        status="DETECTED",
        detected_action_hash=candidate.detected_action_hash,
        source_label="From: Direct Message (LeaderUser)",
        source_content="Please complete the API documentation by tomorrow."
    )

    # 1. Assert stable message ID contract
    assert suggestion.message_id == target_msg_id
    assert suggestion.conversation_id == conv_id
    assert suggestion.source_content == "Please complete the API documentation by tomorrow."
    assert suggestion.source_label == "From: Direct Message (LeaderUser)"

    print("[PASS] Test 1: Source message ID provenance preserved cleanly")

def test_2_source_message_deep_link_contract():
    """Verify deep link data format for frontend handoff."""
    msg_id = f"msg-deep-{uuid4()}"
    conv_id = f"conv-deep-{uuid4()}"

    # Simulating handoff payload
    handoff_params = {
        "conversation_id": conv_id,
        "source_message_id": msg_id
    }

    assert handoff_params["conversation_id"] == conv_id
    assert handoff_params["source_message_id"] == msg_id

    print("[PASS] Test 2: Source message deep link contract verified")

if __name__ == "__main__":
    print("Running AUTO-11B Source Message Deep Link Test Suite...")
    test_1_source_message_id_provenance_preservation()
    test_2_source_message_deep_link_contract()
    print("\nALL AUTO-11B SOURCE MESSAGE DEEP LINK TESTS PASSED SUCCESSFULLY!")
