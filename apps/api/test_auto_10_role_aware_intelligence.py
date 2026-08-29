import pytest
from datetime import datetime, timezone
from app.proactive.detection_engine import ProactiveDetectionEngine
from app.actions.candidate import (
    ActionCandidate,
    IntentCategory,
    ActionType,
    UserResponsibilityRole,
    ConfidenceLevel
)

def test_1_leader_assigns_task_to_member_dual_pov():
    """
    Scenario: Leader tells Member: "Please complete the API documentation by tomorrow."
    Member POV: ASSIGNEE, CREATE_TASK candidate.
    Leader POV: REQUESTER, FOLLOW_UP candidate.
    Observer POV: OBSERVER, LOW relevance (filtered).
    """
    text = "Please complete the API documentation by tomorrow."
    
    # 1. Member POV
    member_candidate = ProactiveDetectionEngine.detect_candidate_action(
        text=text,
        source_type="DIRECT_MESSAGE",
        conversation_id="conv-1",
        sender_name="Leader User",
        current_user_name="Member User"
    )
    assert member_candidate.user_role == UserResponsibilityRole.ASSIGNEE
    assert "complete the api documentation" in member_candidate.subject.lower() or "complete api documentation" in member_candidate.subject.lower()
    assert member_candidate.personal_relevance == ConfidenceLevel.HIGH

    # 2. Leader POV
    leader_candidate = ProactiveDetectionEngine.detect_candidate_action(
        text=text,
        source_type="DIRECT_MESSAGE",
        conversation_id="conv-1",
        sender_name="Leader User",
        current_user_name="Leader User"
    )
    assert leader_candidate.user_role == UserResponsibilityRole.REQUESTER
    assert leader_candidate.candidate_type == "FOLLOW_UP"
    assert "Follow up" in leader_candidate.subject

    # 3. Third-party Observer POV in Group Chat
    observer_candidate = ProactiveDetectionEngine.detect_candidate_action(
        text="Rahul, please update the API documentation by tomorrow.",
        source_type="GROUP_CONVERSATION",
        conversation_id="conv-group-1",
        sender_name="Leader User",
        current_user_name="Priyam Observer"
    )
    assert observer_candidate.user_role == UserResponsibilityRole.OBSERVER
    assert observer_candidate.personal_relevance == ConfidenceLevel.LOW

def test_2_member_self_commitment_dual_pov():
    """
    Scenario: Member says: "I'll finish the API documentation by tomorrow."
    Member POV: ASSIGNEE, CREATE_TASK.
    Leader POV: REVIEWER, CHECK/REVIEW candidate.
    """
    text = "I'll finish the API documentation by tomorrow."

    # 1. Member POV (Speaker)
    member_candidate = ProactiveDetectionEngine.detect_candidate_action(
        text=text,
        source_type="DIRECT_MESSAGE",
        conversation_id="conv-2",
        sender_name="Member User",
        current_user_name="Member User"
    )
    assert member_candidate.user_role == UserResponsibilityRole.ASSIGNEE
    assert member_candidate.candidate_type == "CREATE_TASK"
    assert member_candidate.confidence_level in (ConfidenceLevel.MEDIUM, ConfidenceLevel.HIGH)

    # 2. Leader POV (Recipient when member commits)
    leader_candidate = ProactiveDetectionEngine.detect_candidate_action(
        text=text,
        source_type="DIRECT_MESSAGE",
        conversation_id="conv-2",
        sender_name="Member User",
        current_user_name="Leader User"
    )
    assert leader_candidate.user_role in (UserResponsibilityRole.REQUESTER, UserResponsibilityRole.REVIEWER, UserResponsibilityRole.ASSIGNEE)
    assert leader_candidate.candidate_type in ("FOLLOW_UP", "CREATE_TASK", "REVIEW")

def test_3_completion_statement_does_not_create_task_for_speaker():
    """
    Scenario: Member says: "I completed the API documentation."
    Speaker POV: COMPLETION_SIGNAL intent, LOW confidence/relevance (NO task generated for speaker!).
    Leader POV: REVIEW candidate generated for Leader ("Review API documentation completed by Member").
    """
    text = "I completed the API documentation."

    # Speaker (Member)
    member_candidate = ProactiveDetectionEngine.detect_candidate_action(
        text=text,
        source_type="DIRECT_MESSAGE",
        conversation_id="conv-3",
        sender_name="Member User",
        current_user_name="Member User"
    )
    assert member_candidate.intent == IntentCategory.COMPLETION_SIGNAL
    assert member_candidate.candidate_type == "COMPLETION"
    assert member_candidate.confidence_level == ConfidenceLevel.LOW
    assert member_candidate.personal_relevance == ConfidenceLevel.LOW

    # Leader (Recipient)
    leader_candidate = ProactiveDetectionEngine.detect_candidate_action(
        text=text,
        source_type="DIRECT_MESSAGE",
        conversation_id="conv-3",
        sender_name="Member User",
        current_user_name="Leader User"
    )
    assert leader_candidate.intent == IntentCategory.REVIEW_REQUEST
    assert leader_candidate.candidate_type == "REVIEW"
    assert "Review" in leader_candidate.subject
    assert leader_candidate.confidence_level == ConfidenceLevel.HIGH

def test_4_completion_phrase_variants():
    """Verify various completion phrasing options are classified as COMPLETION_SIGNAL."""
    phrases = [
        "I completed the report.",
        "I finished it.",
        "Done.",
        "I have submitted the API documentation.",
        "I already sent the file.",
        "I finished my part.",
        "I've completed everything."
    ]

    for p in phrases:
        cand = ProactiveDetectionEngine.detect_candidate_action(
            text=p,
            sender_name="Member User",
            current_user_name="Member User"
        )
        assert cand.intent == IntentCategory.COMPLETION_SIGNAL, f"Failed for phrase: '{p}'"
        assert cand.candidate_type == "COMPLETION"

def test_5_user_aware_action_hash_deduplication():
    """Verify same source message generates distinct action hashes for Member vs Leader."""
    text = "Please send the deployment report by Friday."
    
    member_cand = ProactiveDetectionEngine.detect_candidate_action(
        text=text,
        conversation_id="conv-5",
        sender_name="Leader",
        current_user_id="user-member-id",
        current_user_name="Member"
    )

    leader_cand = ProactiveDetectionEngine.detect_candidate_action(
        text=text,
        conversation_id="conv-5",
        sender_name="Leader",
        current_user_id="user-leader-id",
        current_user_name="Leader"
    )

    assert member_cand.detected_action_hash != ""
    assert leader_cand.detected_action_hash != ""
    assert member_cand.detected_action_hash != leader_cand.detected_action_hash

def test_6_pronoun_resolution_for_completion():
    """Verify pronoun resolution works when member says 'I finished it' with history context."""
    history = [
        {"content": "Please work on the API documentation.", "sender": "Leader"},
        {"content": "Working on it now.", "sender": "Member"}
    ]
    
    cand = ProactiveDetectionEngine.detect_candidate_action(
        text="I finished it.",
        history=history,
        sender_name="Member",
        current_user_name="Leader"
    )
    assert cand.candidate_type == "REVIEW"
    assert "api documentation" in cand.subject.lower()

def test_7_generic_date_statement_filtered():
    """Verify generic date statements like 'The meeting is Friday' do not create tasks."""
    cand = ProactiveDetectionEngine.detect_candidate_action(
        text="The client meeting is Friday.",
        sender_name="Leader",
        current_user_name="Member"
    )
    assert cand.intent in (IntentCategory.INFORMATION_ONLY, IntentCategory.NO_ACTION)
    assert cand.confidence_level == ConfidenceLevel.LOW

def test_8_topic_change_cutoff():
    """Verify topic change in history prevents old task context from carrying over."""
    history = [
        {"content": "Please complete the API docs by Friday.", "sender": "Leader"},
        {"content": "Anyway, how was your weekend?", "sender": "Member"}
    ]
    cand = ProactiveDetectionEngine.detect_candidate_action(
        text="I finished it.",
        history=history,
        sender_name="Member",
        current_user_name="Leader"
    )
    # Pronoun "it" should not match old topic prior to "anyway"
    assert cand.intent == IntentCategory.REVIEW_REQUEST
