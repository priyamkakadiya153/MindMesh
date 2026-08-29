import logging
from typing import Optional, List, Tuple
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_, and_

from app.automation.scheduled_automation_model import ScheduledAutomation

logger = logging.getLogger(__name__)

class AutomationResolver:
    """Utility to resolve real ScheduledAutomation records from natural language references."""

    @classmethod
    async def resolve(
        cls,
        target_ref: str,
        user_id: UUID,
        db: AsyncSession
    ) -> Tuple[Optional[ScheduledAutomation], Optional[str]]:
        clean_ref = target_ref.lower().strip()

        # Fetch active & paused automations for user
        stmt = select(ScheduledAutomation).where(
            ScheduledAutomation.user_id == user_id,
            ScheduledAutomation.status != "CANCELLED"
        ).order_by(ScheduledAutomation.created_at.desc())

        res = await db.execute(stmt)
        automations = res.scalars().all()

        if not automations:
            return None, "You don't have any active or paused scheduled automations in your workspace."

        # 1. Check for Ordinal Index Match ("first one", "second one", "1st", "2nd", "automation 1")
        if any(w in clean_ref for w in ["1st", "first", "#1", "1"]):
            if len(automations) >= 1:
                return automations[0], None
        elif any(w in clean_ref for w in ["2nd", "second", "#2", "2"]):
            if len(automations) >= 2:
                return automations[1], None
        elif any(w in clean_ref for w in ["3rd", "third", "#3", "3"]):
            if len(automations) >= 3:
                return automations[2], None

        # 2. Match by exact or partial name
        matches = []
        for auto in automations:
            name_lower = auto.name.lower()
            payload_str = str(auto.action_payload).lower()

            if clean_ref in name_lower or clean_ref in payload_str or clean_ref in auto.schedule_type.lower():
                matches.append(auto)

        if not matches:
            # Substring matching on individual keywords
            ref_words = [w for w in clean_ref.split() if w not in ["my", "the", "a", "an", "automation", "reminder", "task", "message", "to", "for"]]
            for auto in automations:
                name_lower = auto.name.lower()
                if any(w in name_lower for w in ref_words if len(w) > 2):
                    if auto not in matches:
                        matches.append(auto)

        if not matches:
            # Return first automation if only 1 exists
            if len(automations) == 1:
                return automations[0], None
            names = ", ".join([f"'{a.name}'" for a in automations[:3]])
            return None, f"I couldn't find an automation matching '{target_ref}'. Available automations: {names}."

        if len(matches) > 1:
            names = ", ".join([f"'{a.name}' ({a.schedule_type})" for a in matches[:3]])
            return None, f"I found multiple automations matching '{target_ref}': {names}. Please specify which one you want to select."

        return matches[0], None
