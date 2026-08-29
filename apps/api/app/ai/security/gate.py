import time
import uuid
import logging
from typing import Dict, Any, List, Optional, Tuple

from app.ai.security.models import (
    GroundingRequest,
    GroundingResult,
    GroundingStatus,
    PolicyDecision,
    SecuritySeverity,
    SecurityEventType,
    SecurityEvent
)
from app.ai.security.policy import SecurityPolicyEngine
from app.ai.security.grounding import GroundingEvaluator

logger = logging.getLogger(__name__)

class FinalResponseGate:
    """Final Security Gate enforcing fail-closed authorization, secret redaction, and grounding before user delivery."""

    SAFE_FALLBACK_TEXT = "I couldn't safely verify the information needed to answer that question."

    @classmethod
    def evaluate_and_gate(cls, request: GroundingRequest) -> Tuple[PolicyDecision, str, GroundingResult]:
        events: List[SecurityEvent] = []

        # 1. Prompt Injection Check on Query
        is_inj, inj_evt = SecurityPolicyEngine.detect_prompt_injection(
            text=request.query,
            user_id=request.user_id,
            workspace_id=request.workspace_id,
            request_id=request.request_id
        )
        if is_inj and inj_evt:
            events.append(inj_evt)
            res = GroundingResult(
                status=GroundingStatus.SECURITY_BLOCKED,
                decision=PolicyDecision.DENY,
                warnings=["Prompt injection detected in query."],
                security_events=events
            )
            return PolicyDecision.DENY, "I can't process that request due to security policies.", res

        # 2. Workspace Isolation Check on Evidence
        evidence_items = []
        if request.evidence_set and "items" in request.evidence_set:
            evidence_items = request.evidence_set["items"]

        valid_evidence, cross_events = SecurityPolicyEngine.check_workspace_isolation(
            authorized_workspace_id=request.workspace_id,
            evidence_items=evidence_items,
            user_id=request.user_id,
            request_id=request.request_id
        )
        events.extend(cross_events)

        if len(valid_evidence) < len(evidence_items) and len(valid_evidence) == 0:
            res = GroundingResult(
                status=GroundingStatus.SECURITY_BLOCKED,
                decision=PolicyDecision.DENY,
                warnings=["All retrieved evidence belonged to unauthorized workspace."],
                security_events=events
            )
            return PolicyDecision.DENY, "I don't have permission to access that workspace context.", res

        # Update evidence set with authorized items only
        request.evidence_set = {"items": valid_evidence}

        # 3. Grounding & Action Validation
        grounding_res = GroundingEvaluator.evaluate(request)
        grounding_res.security_events.extend(events)

        if grounding_res.decision == PolicyDecision.DENY:
            return PolicyDecision.DENY, cls.SAFE_FALLBACK_TEXT, grounding_res

        # 4. Secret & PII Redaction on Output Content
        raw_content = ""
        if request.answer_result:
            raw_content = request.answer_result.get("content", "")

        sanitized_content = SecurityPolicyEngine.redact_secrets(raw_content)
        if sanitized_content != raw_content:
            evt = SecurityEvent(
                event_id=uuid.uuid4(),
                user_id=request.user_id,
                workspace_id=request.workspace_id,
                request_id=request.request_id,
                event_type=SecurityEventType.SECRET_DETECTED,
                severity=SecuritySeverity.MEDIUM,
                timestamp=time.time(),
                decision=PolicyDecision.REDACT,
                reason_code="SECRET_REDACTED_FROM_OUTPUT"
            )
            grounding_res.security_events.append(evt)

        grounding_res.redacted_content = sanitized_content
        return PolicyDecision.ALLOW, sanitized_content, grounding_res
