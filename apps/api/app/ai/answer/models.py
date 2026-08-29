import time
import uuid
from enum import Enum
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field

class AnswerType(str, Enum):
    DIRECT = "DIRECT"
    EXPLANATION = "EXPLANATION"
    SUMMARY = "SUMMARY"
    COMPARISON = "COMPARISON"
    ANALYSIS = "ANALYSIS"
    RECOMMENDATION = "RECOMMENDATION"
    ACTION_RESULT = "ACTION_RESULT"
    CLARIFICATION = "CLARIFICATION"
    PARTIAL = "PARTIAL"
    NO_RESULT = "NO_RESULT"
    CONFLICT = "CONFLICT"
    ERROR = "ERROR"

class SourceType(str, Enum):
    DOCUMENT = "DOCUMENT"
    FILE = "FILE"
    CONVERSATION = "CONVERSATION"
    MESSAGE = "MESSAGE"
    PROJECT = "PROJECT"
    TASK = "TASK"
    DECISION = "DECISION"
    MEETING = "MEETING"
    KNOWLEDGE = "KNOWLEDGE"
    EXTERNAL_SOURCE = "EXTERNAL_SOURCE"

@dataclass
class CitationItem:
    """Individual Verified Citation."""
    citation_id: str
    source_id: str
    label: str
    source_type: SourceType = SourceType.DOCUMENT
    location: Optional[Dict[str, Any]] = None
    snippet: Optional[str] = None
    relevance: float = 1.0
    authorized: bool = True

    def to_dict(self) -> Dict[str, Any]:
        return {
            "citation_id": self.citation_id,
            "source_id": self.source_id,
            "label": self.label,
            "source_type": self.source_type.value if hasattr(self.source_type, "value") else str(self.source_type),
            "location": self.location,
            "snippet": self.snippet,
            "relevance": self.relevance,
            "authorized": self.authorized
        }

@dataclass
class ClaimCitationMap:
    """Mapping between a factual claim and supporting citations."""
    claim_text: str
    citation_ids: List[str] = field(default_factory=list)
    confidence: str = "HIGH"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "claim_text": self.claim_text,
            "citation_ids": self.citation_ids,
            "confidence": self.confidence
        }

@dataclass
class SourcePolicy:
    """Policy for displaying sources and citations."""
    show_sources: bool = True
    require_citations: bool = True
    max_sources: int = 5
    source_visibility: str = "WORKSPACE"

@dataclass
class AnswerRequest:
    """Request data for Answer Generation & Source Intelligence."""
    request_id: uuid.UUID
    original_query: str
    user_id: uuid.UUID
    workspace_id: uuid.UUID
    conversation_id: Optional[uuid.UUID] = None
    intent: Optional[Dict[str, Any]] = None
    conversation_context: Optional[Dict[str, Any]] = None
    reasoning_result: Optional[Dict[str, Any]] = None
    evidence_set: Optional[Dict[str, Any]] = None
    resolved_entities: List[Dict[str, Any]] = field(default_factory=list)
    action_results: List[Dict[str, Any]] = field(default_factory=list)
    answer_mode: AnswerType = AnswerType.DIRECT
    source_policy: SourcePolicy = field(default_factory=SourcePolicy)

@dataclass
class AnswerResult:
    """Final User-Facing Answer Result."""
    answer_id: uuid.UUID
    content: str
    answer_type: AnswerType
    citations: List[CitationItem] = field(default_factory=list)
    sources: List[Dict[str, Any]] = field(default_factory=list)
    claims: List[ClaimCitationMap] = field(default_factory=list)
    uncertainties: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    action_summary: Optional[str] = None
    follow_up_suggestions: List[str] = field(default_factory=list)
    conflicting_evidence: List[Dict[str, Any]] = field(default_factory=list)
    answer_readiness: str = "READY"
    generation_metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "answer_id": str(self.answer_id),
            "content": self.content,
            "answer_type": self.answer_type.value if hasattr(self.answer_type, "value") else str(self.answer_type),
            "citations": [c.to_dict() for c in self.citations],
            "sources": self.sources,
            "claims": [cl.to_dict() for cl in self.claims],
            "uncertainties": self.uncertainties,
            "warnings": self.warnings,
            "action_summary": self.action_summary,
            "follow_up_suggestions": self.follow_up_suggestions,
            "conflicting_evidence": self.conflicting_evidence,
            "answer_readiness": self.answer_readiness,
            "generation_metadata": self.generation_metadata
        }
