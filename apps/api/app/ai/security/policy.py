import re
import time
import uuid
import logging
from typing import Dict, Any, List, Optional, Tuple

from app.ai.security.models import (
    PolicyDecision,
    SecuritySeverity,
    SecurityEventType,
    SecurityEvent
)

logger = logging.getLogger(__name__)

class SecurityPolicyEngine:
    """Security Policy Engine enforcing authorization, workspace isolation, secret redaction, and prompt injection defense."""

    SECRET_PATTERNS = [
        re.compile(r"sk-[A-Za-z0-9_]{16,}", re.IGNORECASE),
        re.compile(r"bearer\s+[A-Za-z0-9\-\._~\+\/]+=*", re.IGNORECASE),
        re.compile(r"api[_\-]?key\s*=\s*['\"]?[A-Za-z0-9_\-]{16,}['\"]?", re.IGNORECASE),
        re.compile(r"password\s*=\s*['\"]?[^\s'\"]+['\"]?", re.IGNORECASE)
    ]

    INJECTION_PATTERNS = [
        re.compile(r"ignore\s+(all\s+)?(previous\s+)?instructions", re.IGNORECASE),
        re.compile(r"bypass\s+(all\s+)?(security\s+)?rules", re.IGNORECASE),
        re.compile(r"reveal\s+(private\s+)?secrets", re.IGNORECASE),
        re.compile(r"grant\s+myself\s+admin", re.IGNORECASE)
    ]

    @classmethod
    def redact_secrets(cls, text: str) -> str:
        """Redacts API keys, tokens, and passwords from text."""
        sanitized = text
        for pat in cls.SECRET_PATTERNS:
            sanitized = pat.sub("[REDACTED_SECRET]", sanitized)
        return sanitized

    @classmethod
    def check_workspace_isolation(
        cls,
        authorized_workspace_id: uuid.UUID,
        evidence_items: List[Dict[str, Any]],
        user_id: uuid.UUID,
        request_id: uuid.UUID
    ) -> Tuple[List[Dict[str, Any]], List[SecurityEvent]]:
        """Filters evidence to preserve strict workspace isolation."""
        valid_items = []
        events = []

        for item in evidence_items:
            item_ws = item.get("workspace_id")
            if item_ws and str(item_ws) != str(authorized_workspace_id):
                evt = SecurityEvent(
                    event_id=uuid.uuid4(),
                    user_id=user_id,
                    workspace_id=authorized_workspace_id,
                    request_id=request_id,
                    event_type=SecurityEventType.CROSS_WORKSPACE_ATTEMPT,
                    severity=SecuritySeverity.HIGH,
                    timestamp=time.time(),
                    resource_id=str(item.get("source_id", "doc")),
                    decision=PolicyDecision.DENY,
                    reason_code="CROSS_WORKSPACE_LEAKAGE_PREVENTED"
                )
                events.append(evt)
                logger.warning(f"[SecurityPolicyEngine] Blocked cross-workspace item '{item.get('source_id')}'")
            else:
                valid_items.append(item)

        return valid_items, events

    @classmethod
    def detect_prompt_injection(
        cls,
        text: str,
        user_id: uuid.UUID,
        workspace_id: uuid.UUID,
        request_id: uuid.UUID
    ) -> Tuple[bool, Optional[SecurityEvent]]:
        """Detects prompt injection attempts in input query or retrieved data."""
        for pat in cls.INJECTION_PATTERNS:
            if pat.search(text):
                evt = SecurityEvent(
                    event_id=uuid.uuid4(),
                    user_id=user_id,
                    workspace_id=workspace_id,
                    request_id=request_id,
                    event_type=SecurityEventType.PROMPT_INJECTION_DETECTED,
                    severity=SecuritySeverity.HIGH,
                    timestamp=time.time(),
                    decision=PolicyDecision.DENY,
                    reason_code="PROMPT_INJECTION_NEUTRALIZED"
                )
                return True, evt
        return False, None
