import logging
from uuid import UUID
from typing import Dict, Any, List, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from app.governance.policy_store import PolicyStore

logger = logging.getLogger(__name__)

class PolicyEngine:
    @staticmethod
    async def validate_policy(
        db: AsyncSession,
        organization_id: UUID,
        category: str,
        context_data: Dict[str, Any]
    ) -> Tuple[bool, List[str]]:
        """Evaluates inputs/actions against active policy rules, returns (is_allowed, violations)."""
        policies = await PolicyStore.list_policies(db, organization_id, category)
        violations = []

        # Default allowed if no active rules set
        if not policies:
            return True, []

        for policy in policies:
            rules = policy.rules
            
            # 1. Keyword check (Security/Data policy category)
            if "blocked_keywords" in rules and "text" in context_data:
                text_content = str(context_data["text"]).lower()
                for keyword in rules["blocked_keywords"]:
                    if keyword.lower() in text_content:
                        violations.append(f"Blocked keyword '{keyword}' detected under policy '{policy.name}'.")

            # 2. Tool blacklist check (Tool policy category)
            if "blacklisted_tools" in rules and "tool" in context_data:
                tool_name = str(context_data["tool"])
                if tool_name in rules["blacklisted_tools"]:
                    violations.append(f"Tool '{tool_name}' is blacklisted under policy '{policy.name}'.")

            # 3. Privacy / PII check
            if "pii_protection" in rules and rules["pii_protection"] is True and "text" in context_data:
                import re
                email_regex = r"[\w\.-]+@[\w\.-]+\.\w+"
                if re.search(email_regex, str(context_data["text"])):
                    violations.append(f"Potential PII data (email address) detected under policy '{policy.name}'.")

        is_allowed = len(violations) == 0
        return is_allowed, violations
