import asyncio
import sys
import os
from datetime import datetime, timedelta, timezone

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app.proactive.detection_engine import ProactiveDetectionEngine
from app.actions.candidate import IntentCategory, ActionType, ConfidenceLevel

def test_1_critical_regression_overnight_reference_time_stability():
    """
    CRITICAL REGRESSION TEST:
    Message created on 19 Aug 2026 with "I'll complete the API documentation tomorrow."
    Expected stored deadline: 20 Aug 2026.
    Viewing on 20 Aug 2026 or later MUST preserve 20 Aug 2026, NOT recompute to 21 Aug 2026.
    """
    ist_tz = timezone(timedelta(hours=5, minutes=30))
    # Message created on 19 Aug 2026 10:00 AM IST (04:30 AM UTC)
    msg_date = datetime(2026, 8, 19, 4, 30, tzinfo=timezone.utc)

    candidate = ProactiveDetectionEngine.detect_candidate_action(
        text="I'll complete the API documentation tomorrow.",
        source_type="DIRECT_MESSAGE",
        conversation_id="conv-11c-1",
        sender_name="Rahul",
        current_user_name="Rahul",
        message_timestamp=msg_date
    )

    assert candidate is not None
    assert candidate.deadline == "Tomorrow"
    assert candidate.normalized_deadline is not None
    # Check normalized date in IST: 20 Aug 2026
    norm_ist = candidate.normalized_deadline.astimezone(ist_tz)
    assert norm_ist.strftime("%d %b %Y") == "20 Aug 2026"

    print("[PASS] Test 1: Critical overnight reference time stability (19 Aug + 'tomorrow' = 20 Aug 2026)")

def test_2_relative_date_expressions_matrix():
    """Test resolution of relative date expressions against a fixed reference date in Asia/Kolkata timezone."""
    ist_tz = timezone(timedelta(hours=5, minutes=30))
    # Reference date: Thursday, 20 Aug 2026 10:00 AM IST
    ref_time = datetime(2026, 8, 20, 4, 30, tzinfo=timezone.utc)

    # 1. Today -> 20 Aug 2026
    cand_today = ProactiveDetectionEngine.detect_candidate_action(
        text="I will review the pull request today.",
        sender_name="Rahul", current_user_name="Rahul", message_timestamp=ref_time
    )
    assert cand_today.normalized_deadline.astimezone(ist_tz).strftime("%d %b %Y") == "20 Aug 2026"

    # 2. Tomorrow -> 21 Aug 2026
    cand_tomorrow = ProactiveDetectionEngine.detect_candidate_action(
        text="I'll finish the design deck tomorrow.",
        sender_name="Rahul", current_user_name="Rahul", message_timestamp=ref_time
    )
    assert cand_tomorrow.normalized_deadline.astimezone(ist_tz).strftime("%d %b %Y") == "21 Aug 2026"

    # 3. Day after tomorrow -> 22 Aug 2026
    cand_day_after = ProactiveDetectionEngine.detect_candidate_action(
        text="Please complete the deployment day after tomorrow.",
        sender_name="Rahul", current_user_name="Rahul", message_timestamp=ref_time
    )
    assert cand_day_after.normalized_deadline.astimezone(ist_tz).strftime("%d %b %Y") == "22 Aug 2026"

    # 4. In 3 days -> 23 Aug 2026
    cand_in_3 = ProactiveDetectionEngine.detect_candidate_action(
        text="Send me the update in 3 days.",
        sender_name="Rahul", current_user_name="Rahul", message_timestamp=ref_time
    )
    assert cand_in_3.normalized_deadline.astimezone(ist_tz).strftime("%d %b %Y") == "23 Aug 2026"

    # 5. By Friday (from Thursday 20 Aug 2026) -> Friday 21 Aug 2026
    cand_friday = ProactiveDetectionEngine.detect_candidate_action(
        text="Please send the report by Friday.",
        sender_name="Rahul", current_user_name="Rahul", message_timestamp=ref_time
    )
    assert cand_friday.normalized_deadline.astimezone(ist_tz).strftime("%d %b %Y") == "21 Aug 2026"

    print("[PASS] Test 2: Relative date expressions matrix passed")

def test_3_no_invented_time_for_tasks():
    """Verify tasks without explicit time do NOT invent artificial times like 12:00 AM or 09:00 AM in deadline string."""
    ref_time = datetime(2026, 8, 20, 4, 30, tzinfo=timezone.utc)

    # Task without explicit time
    cand_task = ProactiveDetectionEngine.detect_candidate_action(
        text="I will complete the report tomorrow.",
        sender_name="Rahul", current_user_name="Rahul", message_timestamp=ref_time
    )
    assert "12:00 AM" not in cand_task.deadline
    assert "00:00" not in cand_task.deadline
    assert "09:00" not in cand_task.deadline
    assert cand_task.deadline == "Tomorrow"

    print("[PASS] Test 3: No invented time for tasks without explicit time")

if __name__ == "__main__":
    print("Running AUTO-11C Dynamic Date & Time Intelligence Test Suite...")
    test_1_critical_regression_overnight_reference_time_stability()
    test_2_relative_date_expressions_matrix()
    test_3_no_invented_time_for_tasks()
    print("\nALL AUTO-11C DYNAMIC DATE INTELLIGENCE TESTS PASSED SUCCESSFULLY!")
