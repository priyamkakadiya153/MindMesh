import time
import uuid
from enum import Enum
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field

class EvaluationType(str, Enum):
    OFFLINE = "OFFLINE"
    ONLINE = "ONLINE"
    REGRESSION = "REGRESSION"
    END_TO_END = "END_TO_END"
    COMPONENT = "COMPONENT"
    MODEL_BASED = "MODEL_BASED"
    DETERMINISTIC = "DETERMINISTIC"
    PERFORMANCE = "PERFORMANCE"
    SECURITY = "SECURITY"
    GROUNDING = "GROUNDING"

class EvaluationStatus(str, Enum):
    PASS = "PASS"
    PASS_WITH_WARNING = "PASS_WITH_WARNING"
    FAIL = "FAIL"
    ERROR = "ERROR"
    SKIPPED = "SKIPPED"

class FailureCategory(str, Enum):
    INTENT_ERROR = "INTENT_ERROR"
    MEMORY_ERROR = "MEMORY_ERROR"
    RETRIEVAL_ERROR = "RETRIEVAL_ERROR"
    ENTITY_ERROR = "ENTITY_ERROR"
    TOOL_ERROR = "TOOL_ERROR"
    REASONING_ERROR = "REASONING_ERROR"
    ANSWER_ERROR = "ANSWER_ERROR"
    GROUNDING_ERROR = "GROUNDING_ERROR"
    SECURITY_ERROR = "SECURITY_ERROR"
    PERFORMANCE_ERROR = "PERFORMANCE_ERROR"
    UX_ERROR = "UX_ERROR"

class QualityDimension(str, Enum):
    CORRECTNESS = "CORRECTNESS"
    RELEVANCE = "RELEVANCE"
    GROUNDEDNESS = "GROUNDEDNESS"
    COMPLETENESS = "COMPLETENESS"
    CITATION_ACCURACY = "CITATION_ACCURACY"
    SECURITY_COMPLIANCE = "SECURITY_COMPLIANCE"
    LATENCY = "LATENCY"
    COST = "COST"

class ReleaseDecision(str, Enum):
    PASS = "PASS"
    PASS_WITH_WARNING = "PASS_WITH_WARNING"
    BLOCK = "BLOCK"

@dataclass
class GoldenCase:
    """Golden Test Dataset Case."""
    case_id: str
    category: str
    query: str
    expected_intent: str
    expected_entities: List[str] = field(default_factory=list)
    expected_sources: List[str] = field(default_factory=list)
    expected_answer_contains: List[str] = field(default_factory=list)

@dataclass
class RegressionCase:
    """Regression Test Case."""
    case_id: str
    original_issue: str
    query: str
    expected_behavior: str
    status: str = "OPEN"

@dataclass
class MetricResult:
    """Individual Metric Score."""
    metric_name: str
    value: float
    unit: str = "score"
    threshold: Optional[float] = None
    status: EvaluationStatus = EvaluationStatus.PASS

@dataclass
class QualityGate:
    """Rule defining release gate criteria."""
    metric_name: str
    operator: str  # ">=", "<=", "=="
    threshold: float
    severity: str = "CRITICAL"

@dataclass
class EvaluationRequest:
    """Request for evaluating an AI Pipeline trace."""
    evaluation_id: uuid.UUID
    request_id: uuid.UUID
    query: str
    user_id: uuid.UUID
    workspace_id: uuid.UUID
    intent_result: Optional[Dict[str, Any]] = None
    retrieval_result: Optional[Dict[str, Any]] = None
    entity_result: Optional[Dict[str, Any]] = None
    action_results: List[Dict[str, Any]] = field(default_factory=list)
    reasoning_result: Optional[Dict[str, Any]] = None
    answer_result: Optional[Dict[str, Any]] = None
    grounding_result: Optional[Dict[str, Any]] = None
    generation_id: Optional[str] = None
    total_latency_ms: float = 0.0

@dataclass
class EvaluationResult:
    """Final Evaluation Result for an AI request."""
    evaluation_id: uuid.UUID
    status: EvaluationStatus
    overall_score: float
    metrics: Dict[str, MetricResult] = field(default_factory=dict)
    failures: List[FailureCategory] = field(default_factory=list)
    primary_failure: Optional[FailureCategory] = None
    latency_breakdown_ms: Dict[str, float] = field(default_factory=dict)
    token_usage: Dict[str, int] = field(default_factory=dict)
    estimated_cost_usd: float = 0.0
    duplicate_generation_detected: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "evaluation_id": str(self.evaluation_id),
            "status": self.status.value,
            "overall_score": self.overall_score,
            "metrics": {k: v.__dict__ for k, v in self.metrics.items()},
            "failures": [f.value for f in self.failures],
            "primary_failure": self.primary_failure.value if self.primary_failure else None,
            "latency_breakdown_ms": self.latency_breakdown_ms,
            "token_usage": self.token_usage,
            "estimated_cost_usd": self.estimated_cost_usd,
            "duplicate_generation_detected": self.duplicate_generation_detected
        }

@dataclass
class ReleaseEvaluation:
    """Release Decision Summary."""
    decision: ReleaseDecision
    passed_gates: List[str] = field(default_factory=list)
    failed_gates: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
