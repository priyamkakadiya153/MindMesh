import re
import logging
from typing import Dict, Any, List, Optional

from app.ai.security.models import (
    GroundingRequest,
    GroundingResult,
    GroundingStatus,
    PolicyDecision,
    AnswerClaim,
    ClaimType
)

logger = logging.getLogger(__name__)

class GroundingEvaluator:
    """Grounding & Claim Support Evaluator."""

    @classmethod
    def evaluate(cls, request: GroundingRequest) -> GroundingResult:
        content = ""
        if request.answer_result:
            content = request.answer_result.get("content", "")

        reasoning = request.reasoning_result or {}
        readiness = reasoning.get("answer_readiness", "READY")

        # 1. Check Insufficient Evidence
        if readiness == "INSUFFICIENT_EVIDENCE":
            if "couldn't find" not in content.lower() and len(content.split()) > 20:
                return GroundingResult(
                    status=GroundingStatus.UNGROUNDED,
                    decision=PolicyDecision.DENY,
                    warnings=["Generated answer makes unsupported claims despite INSUFFICIENT_EVIDENCE readiness."]
                )

        # 2. Check Action Verification Consistency
        if request.action_results:
            failed_acts = [a for a in request.action_results if a.get("status") in ["FAILED", "WAITING_CONFIRMATION"]]
            if failed_acts:
                if re.search(r"\b(done|created successfully|completed successfully)\b", content, re.IGNORECASE):
                    return GroundingResult(
                        status=GroundingStatus.VALIDATION_FAILED,
                        decision=PolicyDecision.DENY,
                        warnings=["Answer claims successful action completion despite action failure or block."]
                    )

        # 3. Check Certainty Inflation
        if "definitely caused" in content.lower() and "suggests" in reasoning.get("conclusion", "").lower():
            return GroundingResult(
                status=GroundingStatus.VALIDATION_FAILED,
                decision=PolicyDecision.DENY,
                warnings=["Certainty inflation detected: 'definitely caused' unsupported by evidence."]
            )

        # Grounded Success
        claim = AnswerClaim(
            claim_id="claim_1",
            text=content[:100],
            claim_type=ClaimType.FACT,
            confidence=1.0,
            status="SUPPORTED"
        )

        return GroundingResult(
            status=GroundingStatus.GROUNDED,
            decision=PolicyDecision.ALLOW,
            claims=[claim]
        )
