import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

class TrustScorer:
    @staticmethod
    def calculate_trust_score(
        knowledge_quality: float,
        retrieval_confidence: float,
        policy_compliance: float,
        tool_reliability: float,
        workflow_success: float
    ) -> float:
        """Calculates a composite trust score range 0.0 -> 1.0 based on criteria."""
        # Clean inputs
        kq = max(0.0, min(1.0, knowledge_quality))
        rc = max(0.0, min(1.0, retrieval_confidence))
        pc = max(0.0, min(1.0, policy_compliance))
        tr = max(0.0, min(1.0, tool_reliability))
        ws = max(0.0, min(1.0, workflow_success))

        # Weight Distribution Formula
        score = (kq * 0.25) + (rc * 0.25) + (pc * 0.20) + (tr * 0.15) + (ws * 0.15)
        
        return round(score, 4)
