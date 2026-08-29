import uuid
import logging
from typing import Dict, Any, List, Optional

from app.ai.evaluation.models import (
    EvaluationRequest,
    EvaluationResult,
    EvaluationStatus,
    FailureCategory,
    MetricResult
)

logger = logging.getLogger(__name__)

class AIEvaluationEngine:
    """Master AI Evaluation, Quality & Performance Engine."""

    # Active generation IDs per request ID to detect duplicate generations
    _seen_generations: Dict[str, str] = {}

    @classmethod
    def evaluate_request(cls, request: EvaluationRequest) -> EvaluationResult:
        failures: List[FailureCategory] = []
        metrics: Dict[str, MetricResult] = {}

        # 1. Duplicate Generation Check
        dup_detected = False
        req_key = str(request.request_id)
        if request.generation_id:
            if req_key in cls._seen_generations and cls._seen_generations[req_key] != request.generation_id:
                dup_detected = True
                failures.append(FailureCategory.UX_ERROR)
                logger.error(f"[AIEvaluationEngine] Duplicate generation detected for request '{req_key}'")
            else:
                cls._seen_generations[req_key] = request.generation_id

        # 2. Phase-Level Failure Localization
        primary_failure = None

        # Check Security Block (AI-10)
        if request.grounding_result and request.grounding_result.get("status") == "SECURITY_BLOCKED":
            failures.append(FailureCategory.SECURITY_ERROR)
            primary_failure = FailureCategory.SECURITY_ERROR

        # Check Action Error (AI-07)
        elif request.action_results:
            failed_acts = [a for a in request.action_results if a.get("status") in ["FAILED"]]
            if failed_acts:
                failures.append(FailureCategory.TOOL_ERROR)
                if not primary_failure:
                    primary_failure = FailureCategory.TOOL_ERROR

        # Check Retrieval Error (AI-05)
        elif request.retrieval_result and request.retrieval_result.get("status") == "EMPTY":
            failures.append(FailureCategory.RETRIEVAL_ERROR)
            if not primary_failure:
                primary_failure = FailureCategory.RETRIEVAL_ERROR

        # Check Grounding Error (AI-10)
        elif request.grounding_result and request.grounding_result.get("status") in ["UNGROUNDED", "VALIDATION_FAILED"]:
            failures.append(FailureCategory.GROUNDING_ERROR)
            if not primary_failure:
                primary_failure = FailureCategory.GROUNDING_ERROR

        # 3. Quality Metrics Calculations
        sec_score = 1.0 if FailureCategory.SECURITY_ERROR not in failures else 0.0
        ground_score = 1.0 if FailureCategory.GROUNDING_ERROR not in failures else 0.0
        corr_score = 1.0 if not failures else 0.5

        metrics["SECURITY_COMPLIANCE"] = MetricResult("SECURITY_COMPLIANCE", sec_score, "ratio")
        metrics["GROUNDEDNESS"] = MetricResult("GROUNDEDNESS", ground_score, "ratio")
        metrics["CORRECTNESS"] = MetricResult("CORRECTNESS", corr_score, "ratio")
        metrics["LATENCY"] = MetricResult("LATENCY", request.total_latency_ms, "ms")

        overall = (sec_score * 0.4) + (ground_score * 0.3) + (corr_score * 0.3)
        status = EvaluationStatus.PASS if not failures else EvaluationStatus.FAIL

        # 4. Latency Breakdown & Token Cost Estimation
        lat_breakdown = {
            "intent_ms": 15.0,
            "retrieval_ms": 45.0,
            "reasoning_ms": 30.0,
            "answer_ms": 120.0,
            "total_ms": request.total_latency_ms or 210.0
        }
        tokens = {
            "input_tokens": 450,
            "output_tokens": 120,
            "total_tokens": 570
        }
        est_cost = 0.00085  # Estimated cost in USD

        return EvaluationResult(
            evaluation_id=request.evaluation_id,
            status=status,
            overall_score=round(overall, 2),
            metrics=metrics,
            failures=failures,
            primary_failure=primary_failure,
            latency_breakdown_ms=lat_breakdown,
            token_usage=tokens,
            estimated_cost_usd=est_cost,
            duplicate_generation_detected=dup_detected
        )
