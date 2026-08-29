import logging
from typing import List, Dict, Any
from app.agents.exceptions import AgentException

logger = logging.getLogger(__name__)

class ConflictResolver:
    @staticmethod
    def resolve(outputs: List[Dict[str, Any]], match_key: str = "status") -> Dict[str, Any]:
        """Resolves conflicting agent outputs using confidence levels and metadata comparisons."""
        if not outputs:
            raise AgentException("ConflictResolver: Cannot resolve empty list of outputs.")

        logger.warning(f"ConflictResolver: Initiating conflict resolution for {len(outputs)} inputs.")

        # 1. Compare confidence scores
        best_output = None
        max_confidence = -1.0
        
        for out in outputs:
            # Check custom confidence score or default
            target = out.get("result", out) if isinstance(out, dict) else out
            conf = float(target.get("confidence", target.get("confidence_score", 0.0)))
            if conf > max_confidence:
                max_confidence = conf
                best_output = out

        # If we have a single winner with clear superior confidence
        confidences = []
        for out in outputs:
            target = out.get("result", out) if isinstance(out, dict) else out
            confidences.append(float(target.get("confidence", target.get("confidence_score", 0.0))))
        if confidences.count(max_confidence) == 1 and best_output:
            logger.info(f"ConflictResolver: Resolved conflict using confidence winner (score: {max_confidence})")
            return {
                "resolved": True,
                "resolution_method": "CONFIDENCE_SCORE",
                "output": best_output
            }

        # 2. Compare evidence details/length
        best_output = None
        max_evidence_len = -1
        
        for out in outputs:
            target = out.get("result", out) if isinstance(out, dict) else out
            evidence = str(target.get("details", target.get("synthesis", "")))
            evidence_len = len(evidence)
            if evidence_len > max_evidence_len:
                max_evidence_len = evidence_len
                best_output = out

        evidence_lens = []
        for out in outputs:
            target = out.get("result", out) if isinstance(out, dict) else out
            evidence_lens.append(len(str(target.get("details", target.get("synthesis", "")))))
        if evidence_lens.count(max_evidence_len) == 1 and best_output:
            logger.info(f"ConflictResolver: Resolved conflict using evidence details length winner (len: {max_evidence_len})")
            return {
                "resolved": True,
                "resolution_method": "EVIDENCE_COMPILATION_LENGTH",
                "output": best_output
            }

        # 3. Escalation fallback
        logger.error("ConflictResolver: Unable to resolve conflict automatically. Escalating to Supervisor.")
        raise AgentException(
            "ConflictResolver: Unable to resolve agent disagreements automatically. Escalation to Supervisor is required."
        )
