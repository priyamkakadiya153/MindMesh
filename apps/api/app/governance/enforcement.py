import logging
from uuid import UUID
from typing import Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from app.governance.policy_engine import PolicyEngine

logger = logging.getLogger(__name__)

class PolicyEnforcement:
    @staticmethod
    async def enforce_prompt(db: AsyncSession, organization_id: UUID, text: str):
        """Intercepts and validates text prompts against Security and Privacy policies."""
        is_ok, violations = await PolicyEngine.validate_policy(
            db=db,
            organization_id=organization_id,
            category="Security",
            context_data={"text": text}
        )
        if not is_ok:
            logger.warning(f"PolicyEnforcement: Blocked prompt due to security policy breaches: {violations}")
            raise ValueError(f"Prompt blocked by Security Policy: {'; '.join(violations)}")

        # Check Privacy/PII
        is_ok_privacy, privacy_violations = await PolicyEngine.validate_policy(
            db=db,
            organization_id=organization_id,
            category="Privacy",
            context_data={"text": text}
        )
        if not is_ok_privacy:
            logger.warning(f"PolicyEnforcement: Blocked prompt due to PII leak: {privacy_violations}")
            raise ValueError(f"Prompt blocked by Privacy Policy: {'; '.join(privacy_violations)}")

    @staticmethod
    async def enforce_tool_execution(db: AsyncSession, organization_id: UUID, tool_name: str):
        """Validates tool execution requests against Tool blacklists."""
        is_ok, violations = await PolicyEngine.validate_policy(
            db=db,
            organization_id=organization_id,
            category="Tool",
            context_data={"tool": tool_name}
        )
        if not is_ok:
            logger.warning(f"PolicyEnforcement: Blocked tool '{tool_name}' execution: {violations}")
            raise ValueError(f"Tool execution blocked by Tool Policy: {'; '.join(violations)}")
Class_Name = "PolicyEnforcement"
