import asyncio
import sys
import os
from datetime import datetime, timezone, timedelta

# Add apps/api to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../apps/api')))

from app.actions.classifier import ActionClassifier
from app.actions.types import ActionIntentType, ActionStatus, ActionResultStatus
from app.notifications.time_parser import NaturalTimeParser
from app.actions.executors.task_update_executor import UpdateTaskActionExecutor
from app.actions.executors.task_assign_executor import AssignTaskActionExecutor
from app.actions.executors.task_complete_executor import CompleteTaskActionExecutor

def test_task_operations_classification():
    # 1. Update task
    prop_upd = ActionClassifier.classify("Change the API task deadline to Friday.")
    assert prop_upd is not None
    assert prop_upd.intent_type == ActionIntentType.UPDATE_TASK
    assert prop_upd.parameters.get("task_name") == "API"
    print("[PASS] Update Task Classification test")

    # 2. Assign task
    prop_ass = ActionClassifier.classify("Assign the API integration task to Dhruvil.")
    assert prop_ass is not None
    assert prop_ass.intent_type == ActionIntentType.ASSIGN_TASK
    assert prop_ass.parameters.get("assignee_name") == "Dhruvil"
    print("[PASS] Assign Task Classification test")

    # 3. Complete task
    prop_comp = ActionClassifier.classify("Mark the API integration task as complete.")
    assert prop_comp is not None
    assert prop_comp.intent_type == ActionIntentType.COMPLETE_TASK
    assert "API integration" in prop_comp.parameters.get("task_name")
    print("[PASS] Complete Task Classification test")

def test_natural_time_parsing():
    # 1. "in 10 minutes"
    utc_dt, time_str = NaturalTimeParser.parse_time("in 10 minutes")
    assert utc_dt > datetime.now(timezone.utc)
    print(f"[PASS] Natural Time Parsing ('in 10 minutes' -> {time_str})")

    # 2. "tomorrow at 10 AM"
    utc_dt_tom, time_str_tom = NaturalTimeParser.parse_time("tomorrow at 10 AM")
    assert utc_dt_tom > datetime.now(timezone.utc)
    print(f"[PASS] Natural Time Parsing ('tomorrow at 10 AM' -> {time_str_tom})")

def test_reminder_classification():
    # 1. Create reminder
    prop_rem = ActionClassifier.classify("Remind me tomorrow at 10 AM to submit the report.")
    assert prop_rem is not None
    assert prop_rem.intent_type == ActionIntentType.CREATE_REMINDER
    assert "submit the report" in prop_rem.parameters.get("reminder_text").lower()
    print("[PASS] Create Reminder Classification test")

    # 2. View reminders query returns None (read-only query separation)
    prop_view = ActionClassifier.classify("What reminders do I have?")
    assert prop_view is None
    print("[PASS] View Reminders Question Separation test")

    # 3. Cancel reminder
    prop_can = ActionClassifier.classify("Cancel my report reminder.")
    assert prop_can is not None
    assert prop_can.parameters.get("is_cancel_action") is True
    print("[PASS] Cancel Reminder Classification test")

if __name__ == "__main__":
    print("Running AUTO-02 Task & Reminder Actions Test Suite...")
    test_task_operations_classification()
    test_natural_time_parsing()
    test_reminder_classification()
    print("ALL AUTO-02 BACKEND TESTS PASSED SUCCESSFULLY!")
