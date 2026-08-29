import asyncio
import sys
import os
from uuid import uuid4
from datetime import datetime, timezone

# Add apps/api to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../apps/api')))

import app.models
from app.models.user import User
from app.models.task import Task
from app.notifications.reminder_model import Reminder
from app.models.conversations import DirectMessage, Conversation
from app.automation.scheduled_automation_model import ScheduledAutomation
from app.actions.types import ActionIntentType, ActionProposal, ActionResult, ActionResultStatus
from app.actions.classifier import ActionClassifier
from app.ai.rag.formatter import RAGFormatter

def test_user_organization_id_property():
    u = User(id=uuid4(), email="test@mindmesh.com", username="testuser")
    org_id = uuid4()
    u.current_organization_id = org_id
    assert u.organization_id == org_id
    print("[PASS] User organization_id property test")

def test_action_classifier_management_intents():
    # 1. Pause Intent
    p_pause = ActionClassifier.classify("Pause my weekly task review")
    assert p_pause is not None
    assert p_pause.intent_type == ActionIntentType.PAUSE_AUTOMATION
    assert p_pause.parameters.get("management_action") == "PAUSE"

    # 2. Resume Intent
    p_resume = ActionClassifier.classify("Resume my weekly task review")
    assert p_resume is not None
    assert p_resume.intent_type == ActionIntentType.RESUME_AUTOMATION
    assert p_resume.parameters.get("management_action") == "RESUME"

    # 3. Update Intent
    p_update = ActionClassifier.classify("Change my weekly task review to Tuesday at 10 AM")
    assert p_update is not None
    assert p_update.intent_type == ActionIntentType.UPDATE_AUTOMATION
    assert p_update.parameters.get("management_action") == "UPDATE"

    # 4. Read Reminders
    p_rem = ActionClassifier.classify("What reminders do I have?")
    assert p_rem is not None
    assert p_rem.parameters.get("is_view_query") is True

    # 5. Read Automations
    p_auto = ActionClassifier.classify("What automations do I have?")
    assert p_auto is not None
    assert p_auto.parameters.get("is_view_query") is True

    # 6. Read Action History
    p_hist = ActionClassifier.classify("What did AI do for me today?")
    assert p_hist is not None
    assert p_hist.parameters.get("is_history_query") is True

    print("[PASS] ActionClassifier intent & query classification tests")

def test_rag_formatter_prompt_leak_sanitization():
    raw = "You are MindMesh AI, an enterprise Knowledge Intelligence assistant.\nHere is the real answer to your question."
    clean, _ = RAGFormatter.format_response(raw, citations=[])
    assert "You are MindMesh AI" not in clean
    assert "Here is the real answer" in clean
    print("[PASS] RAGFormatter system prompt leak sanitization test")

if __name__ == "__main__":
    print("Running AUTO-FIX-01 Action & Database Integrity Test Suite...")
    test_user_organization_id_property()
    test_action_classifier_management_intents()
    test_rag_formatter_prompt_leak_sanitization()
    print("ALL AUTO-FIX-01 BACKEND TESTS PASSED SUCCESSFULLY!")
