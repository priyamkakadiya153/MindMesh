import logging
from typing import Dict, Any, List, Optional
from app.ai.evaluation.models import (
    EvaluationResult,
    QualityGate,
    ReleaseDecision,
    ReleaseEvaluation
)

logger = logging.getLogger(__name__)

class ReleaseEvaluator:
    """Evaluates Quality Gate policies to determine AI Release Candidate readiness."""

    DEFAULT_GATES: List[QualityGate] = [
        QualityGate("SECURITY_COMPLIANCE", "==", 1.0, "CRITICAL"),
        QualityGate("GROUNDEDNESS", ">=", 0.85, "CRITICAL"),
        QualityGate("CORRECTNESS", ">=", 0.80, "HIGH"),
        QualityGate("LATENCY", "<=", 5000.0, "MEDIUM")
    ]

    @classmethod
    def evaluate_release(
        cls,
        eval_results: List[EvaluationResult],
        gates: Optional[List[QualityGate]] = None
    ) -> ReleaseEvaluation:
        active_gates = gates or cls.DEFAULT_GATES
        passed = []
        failed = []
        warnings = []

        if not eval_results:
            return ReleaseEvaluation(
                decision=ReleaseDecision.BLOCK,
                warnings=["Zero evaluation results available for release evaluation."]
            )

        # Average metrics calculation
        avg_sec = sum(r.metrics.get("SECURITY_COMPLIANCE", type("obj", (), {"value": 1.0})()).value for r in eval_results) / len(eval_results)
        avg_ground = sum(r.metrics.get("GROUNDEDNESS", type("obj", (), {"value": 1.0})()).value for r in eval_results) / len(eval_results)
        avg_corr = sum(r.metrics.get("CORRECTNESS", type("obj", (), {"value": 1.0})()).value for r in eval_results) / len(eval_results)
        avg_lat = sum(r.metrics.get("LATENCY", type("obj", (), {"value": 100.0})()).value for r in eval_results) / len(eval_results)

        scores = {
            "SECURITY_COMPLIANCE": avg_sec,
            "GROUNDEDNESS": avg_ground,
            "CORRECTNESS": avg_corr,
            "LATENCY": avg_lat
        }

        has_critical_failure = False

        for gate in active_gates:
            val = scores.get(gate.metric_name, 0.0)
            ok = False
            if gate.operator == "==":
                ok = (val == gate.threshold)
            elif gate.operator == ">=":
                ok = (val >= gate.threshold)
            elif gate.operator == "<=":
                ok = (val <= gate.threshold)

            gate_str = f"{gate.metric_name} {gate.operator} {gate.threshold} (Actual: {val})"
            if ok:
                passed.append(gate_str)
            else:
                failed.append(gate_str)
                if gate.severity == "CRITICAL":
                    has_critical_failure = True
                else:
                    warnings.append(f"Gate warning: {gate_str}")

        if has_critical_failure:
            decision = ReleaseDecision.BLOCK
        elif failed:
            decision = ReleaseDecision.PASS_WITH_WARNING
        else:
            decision = ReleaseDecision.PASS

        return ReleaseEvaluation(
            decision=decision,
            passed_gates=passed,
            failed_gates=failed,
            warnings=warnings
        )
