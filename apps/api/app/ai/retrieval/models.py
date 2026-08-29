import time
import uuid
from enum import Enum
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field

class SourceType(str, Enum):
    DOCUMENT = "DOCUMENT"
    CONVERSATION = "CONVERSATION"
    MESSAGE = "MESSAGE"
    PROJECT = "PROJECT"
    TASK = "TASK"
    DECISION = "DECISION"
    KNOWLEDGE = "KNOWLEDGE"
    USER = "USER"
    TEAM = "TEAM"

class RetrievalMode(str, Enum):
    AUTO = "AUTO"
    SEMANTIC = "SEMANTIC"
    KEYWORD = "KEYWORD"
    STRUCTURED = "STRUCTURED"
    CONVERSATION = "CONVERSATION"
    DOCUMENT = "DOCUMENT"
    MULTI_SOURCE = "MULTI_SOURCE"

class EvidenceCoverage(str, Enum):
    GOOD = "GOOD"
    PARTIAL = "PARTIAL"
    WEAK = "WEAK"
    NONE = "NONE"

@dataclass
class RetrievalRequest:
    """Input payload for Hybrid Knowledge Retrieval."""
    request_id: str
    original_query: str
    user_id: uuid.UUID
    organization_id: uuid.UUID
    workspace_id: Optional[uuid.UUID] = None
    conversation_id: Optional[uuid.UUID] = None
    normalized_query: Optional[str] = None
    intent_result: Optional[Any] = None
    conversation_context: Optional[Any] = None
    scope: str = "WORKSPACE"
    time_range: Optional[Dict[str, Any]] = None
    source_hints: List[SourceType] = field(default_factory=list)
    filters: Dict[str, Any] = field(default_factory=dict)
    mode: RetrievalMode = RetrievalMode.AUTO
    max_results: int = 10
    latency_budget_ms: int = 2000

@dataclass
class RetrievalPlan:
    """Executable strategy created by RetrievalPlanner."""
    sources: List[SourceType]
    queries: List[str]
    filters: Dict[str, Any] = field(default_factory=dict)
    time_range: Optional[Dict[str, Any]] = None
    max_results: int = 10
    rerank_required: bool = True
    fallback_strategy: str = "KEYWORD"

@dataclass
class EvidenceItem:
    """Normalized evidence handoff object for downstream reasoning."""
    source_id: str
    source_type: SourceType
    title: str
    content: str
    score: float = 0.0
    authority_score: float = 0.5
    recency_score: float = 0.5
    location: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    retrieval_methods: List[str] = field(default_factory=list)
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "source_id": self.source_id,
            "source_type": self.source_type.value if hasattr(self.source_type, "value") else str(self.source_type),
            "title": self.title,
            "content": self.content,
            "score": round(self.score, 4),
            "authority_score": round(self.authority_score, 2),
            "recency_score": round(self.recency_score, 2),
            "location": self.location,
            "metadata": self.metadata,
            "retrieval_methods": self.retrieval_methods,
            "timestamp": self.timestamp
        }

@dataclass
class EvidenceSet:
    """Final output container of Hybrid Knowledge Retrieval Engine."""
    query: str
    items: List[EvidenceItem] = field(default_factory=list)
    coverage: EvidenceCoverage = EvidenceCoverage.GOOD
    confidence: str = "STRONG"
    latency_ms: int = 0
    sources_attempted: List[SourceType] = field(default_factory=list)
    sources_succeeded: List[SourceType] = field(default_factory=list)
    trace: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "query": self.query,
            "coverage": self.coverage.value if hasattr(self.coverage, "value") else str(self.coverage),
            "confidence": self.confidence,
            "latency_ms": self.latency_ms,
            "items_count": len(self.items),
            "items": [item.to_dict() for item in self.items],
            "sources_attempted": [s.value if hasattr(s, "value") else str(s) for s in self.sources_attempted],
            "sources_succeeded": [s.value if hasattr(s, "value") else str(s) for s in self.sources_succeeded],
            "trace": self.trace
        }
