from enum import Enum
from typing import Dict, Any, Optional
from dataclasses import dataclass
from app.actions.types import ActionIntentType

class ActionRiskLevel(str, Enum):
    LEVEL_0_READ_ONLY = "LEVEL_0_READ_ONLY"       # List, get, search, count, view (No confirmation)
    LEVEL_1_LOW_RISK = "LEVEL_1_LOW_RISK"         # Create task, update task, create reminder, pause/resume auto (Confirmation required)
    LEVEL_2_EXTERNAL = "LEVEL_2_EXTERNAL"         # Send DM, create scheduled DM, update recipient (Always confirmation)
    LEVEL_3_DESTRUCTIVE = "LEVEL_3_DESTRUCTIVE"   # Delete project, delete document, remove member (Blocked by default)

@dataclass
class PolicyEvaluation:
    risk_level: ActionRiskLevel
    confirmation_required: bool
    is_blocked: bool
    block_reason: Optional[str] = None
    expiration_minutes: int = 15
    action_button_label: str = "Confirm Action"

class ActionSafetyPolicy:
    """Centralized Safety & Confirmation Policy for all MindMesh AI Actions."""

    _ACTION_RISK_MAP: Dict[ActionIntentType, ActionRiskLevel] = {
        # Low-risk reversible actions
        ActionIntentType.CREATE_TASK: ActionRiskLevel.LEVEL_1_LOW_RISK,
        ActionIntentType.UPDATE_TASK: ActionRiskLevel.LEVEL_1_LOW_RISK,
        ActionIntentType.ASSIGN_TASK: ActionRiskLevel.LEVEL_1_LOW_RISK,
        ActionIntentType.COMPLETE_TASK: ActionRiskLevel.LEVEL_1_LOW_RISK,
        ActionIntentType.CREATE_REMINDER: ActionRiskLevel.LEVEL_1_LOW_RISK,
        ActionIntentType.CREATE_AUTOMATION: ActionRiskLevel.LEVEL_1_LOW_RISK,

        # Externally visible actions
        ActionIntentType.SEND_DIRECT_MESSAGE: ActionRiskLevel.LEVEL_2_EXTERNAL,

        # High-risk / Destructive actions
        ActionIntentType.DELETE_DOCUMENT: ActionRiskLevel.LEVEL_3_DESTRUCTIVE,
    }

    _BUTTON_LABELS: Dict[ActionIntentType, str] = {
        ActionIntentType.CREATE_TASK: "Create Task",
        ActionIntentType.UPDATE_TASK: "Update Task",
        ActionIntentType.CREATE_REMINDER: "Set Reminder",
        ActionIntentType.SEND_DIRECT_MESSAGE: "Send Message",
        ActionIntentType.CREATE_AUTOMATION: "Create Automation",
        ActionIntentType.DELETE_DOCUMENT: "Delete Document",
    }

    @classmethod
    def evaluate(cls, intent_type: ActionIntentType, parameters: Optional[Dict[str, Any]] = None) -> PolicyEvaluation:
        params = parameters or {}
        risk_level = cls._ACTION_RISK_MAP.get(intent_type, ActionRiskLevel.LEVEL_1_LOW_RISK)

        # Check for specific management actions
        mgmt_action = params.get("management_action")
        if mgmt_action == "CANCEL":
            risk_level = ActionRiskLevel.LEVEL_1_LOW_RISK
        elif mgmt_action in ["PAUSE", "RESUME", "UPDATE"]:
            risk_level = ActionRiskLevel.LEVEL_1_LOW_RISK

        # Check for view/read-only query flag
        if params.get("is_view_query") or params.get("is_read_only"):
            risk_level = ActionRiskLevel.LEVEL_0_READ_ONLY

        # Level 3 Destructive Actions are BLOCKED by default
        if risk_level == ActionRiskLevel.LEVEL_3_DESTRUCTIVE:
            return PolicyEvaluation(
                risk_level=risk_level,
                confirmation_required=False,
                is_blocked=True,
                block_reason="Destructive actions (such as document or project deletion) are disabled via AI Chat for system safety.",
                action_button_label="Blocked"
            )

        # Level 0 Read-Only does NOT require confirmation
        if risk_level == ActionRiskLevel.LEVEL_0_READ_ONLY:
            return PolicyEvaluation(
                risk_level=risk_level,
                confirmation_required=False,
                is_blocked=False,
                action_button_label="View"
            )

        # Level 1 & Level 2 require confirmation
        button_label = cls._BUTTON_LABELS.get(intent_type, "Confirm Action")
        if mgmt_action:
            button_label = f"{mgmt_action.title()} Automation"

        return PolicyEvaluation(
            risk_level=risk_level,
            confirmation_required=True,
            is_blocked=False,
            expiration_minutes=15,
            action_button_label=button_label
        )
