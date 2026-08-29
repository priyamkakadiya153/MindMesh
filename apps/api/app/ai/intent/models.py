from enum import Enum
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field

class IntentType(str, Enum):
    GREETING = "GREETING"
    GENERAL_KNOWLEDGE = "GENERAL_KNOWLEDGE"
    WORKSPACE_QUERY = "WORKSPACE_QUERY"
    DOCUMENT_QUERY = "DOCUMENT_QUERY"
    PROJECT_QUERY = "PROJECT_QUERY"
    TASK_QUERY = "TASK_QUERY"
    DECISION_QUERY = "DECISION_QUERY"
    CONVERSATION_QUERY = "CONVERSATION_QUERY"
    MEETING_QUERY = "MEETING_QUERY"
    SEARCH_QUERY = "SEARCH_QUERY"
    SUMMARY_REQUEST = "SUMMARY_REQUEST"
    EXTRACTION_REQUEST = "EXTRACTION_REQUEST"
    COMPARISON_REQUEST = "COMPARISON_REQUEST"
    EXPLANATION_REQUEST = "EXPLANATION_REQUEST"
    FOLLOW_UP = "FOLLOW_UP"
    CLARIFICATION = "CLARIFICATION"
    AMBIGUOUS = "AMBIGUOUS"
    ACTION_REQUEST = "ACTION_REQUEST"
    STATUS_REQUEST = "STATUS_REQUEST"
    NAVIGATION_REQUEST = "NAVIGATION_REQUEST"
    FEEDBACK = "FEEDBACK"
    THANKS = "THANKS"
    OTHER = "OTHER"
    UNKNOWN = "UNKNOWN"

class QueryType(str, Enum):
    QUESTION = "QUESTION"
    REQUEST = "REQUEST"
    COMMAND = "COMMAND"
    SEARCH = "SEARCH"
    SUMMARY = "SUMMARY"
    COMPARISON = "COMPARISON"
    NAVIGATION = "NAVIGATION"
    FEEDBACK = "FEEDBACK"
    CONVERSATION = "CONVERSATION"

class ScopeType(str, Enum):
    USER = "USER"
    CONVERSATION = "CONVERSATION"
    PROJECT = "PROJECT"
    WORKSPACE = "WORKSPACE"
    ORGANIZATION = "ORGANIZATION"
    DOCUMENT = "DOCUMENT"
    TASK = "TASK"
    DECISION = "DECISION"
    MEETING = "MEETING"
    GENERAL = "GENERAL"

class ConfidenceLevel(str, Enum):
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"

class QueryComplexity(str, Enum):
    SIMPLE = "SIMPLE"
    MODERATE = "MODERATE"
    COMPLEX = "COMPLEX"

class EntitySource(str, Enum):
    EXPLICIT = "EXPLICIT"
    CONTEXTUAL = "CONTEXTUAL"
    INFERRED = "INFERRED"
    UNKNOWN = "UNKNOWN"

@dataclass
class EntityMention:
    text: str
    type: str  # Person, Project, Task, Document, Meeting, Decision, Technology, Workspace
    source: EntitySource = EntitySource.EXPLICIT
    position: Optional[int] = None
    confidence: ConfidenceLevel = ConfidenceLevel.HIGH

@dataclass
class TemporalConstraint:
    raw_expression: str
    relative_days: Optional[int] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    granularity: Optional[str] = None  # day, week, month, year

@dataclass
class AmbiguityDetail:
    type: str  # Entity, Scope, Temporal, Action, Reference, Intent
    reason: str
    candidates: List[str] = field(default_factory=list)
    clarification_prompt: Optional[str] = None

@dataclass
class ActionDetail:
    verb: str  # CREATE, UPDATE, DELETE, OPEN, RENAME, ARCHIVE
    target: str  # TASK, PROJECT, DOCUMENT, CONVERSATION, DECISION
    parameters: Dict[str, Any] = field(default_factory=dict)
    constraints: Dict[str, Any] = field(default_factory=dict)

@dataclass
class RoutingHints:
    needs_general_model: bool = False
    needs_workspace_retrieval: bool = False
    needs_structured_data: bool = False
    needs_document_search: bool = False
    needs_conversation_search: bool = False
    needs_graph: bool = False
    needs_tool: bool = False
    needs_multi_step_reasoning: bool = False
    needs_clarification: bool = False

@dataclass
class IntentResult:
    """Normalized Intent & Query Understanding Output Model."""
    intent: IntentType
    sub_intents: List[IntentType] = field(default_factory=list)
    confidence: ConfidenceLevel = ConfidenceLevel.HIGH
    query: str = ""
    normalized_query: str = ""
    rewritten_query: Optional[str] = None
    query_type: QueryType = QueryType.QUESTION
    scope: ScopeType = ScopeType.GENERAL
    entities: List[EntityMention] = field(default_factory=list)
    references: List[str] = field(default_factory=list)
    temporal: Optional[TemporalConstraint] = None
    requires_retrieval: bool = False
    source_hints: List[str] = field(default_factory=list)
    requires_conversation_context: bool = False
    requires_tool: bool = False
    action_details: Optional[ActionDetail] = None
    requires_clarification: bool = False
    ambiguities: List[AmbiguityDetail] = field(default_factory=list)
    language: str = "English"
    complexity: QueryComplexity = QueryComplexity.SIMPLE
    routing_hints: RoutingHints = field(default_factory=RoutingHints)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "intent": self.intent.value,
            "sub_intents": [i.value for i in self.sub_intents],
            "confidence": self.confidence.value,
            "query": self.query,
            "normalized_query": self.normalized_query,
            "rewritten_query": self.rewritten_query,
            "query_type": self.query_type.value,
            "scope": self.scope.value,
            "entities": [{"text": e.text, "type": e.type, "source": e.source.value} for e in self.entities],
            "references": self.references,
            "temporal": {
                "raw_expression": self.temporal.raw_expression,
                "relative_days": self.temporal.relative_days,
            } if self.temporal else None,
            "requires_retrieval": self.requires_retrieval,
            "source_hints": self.source_hints,
            "requires_conversation_context": self.requires_conversation_context,
            "requires_tool": self.requires_tool,
            "action_details": {
                "verb": self.action_details.verb,
                "target": self.action_details.target,
                "parameters": self.action_details.parameters,
            } if self.action_details else None,
            "requires_clarification": self.requires_clarification,
            "ambiguities": [
                {"type": a.type, "reason": a.reason, "candidates": a.candidates, "clarification_prompt": a.clarification_prompt}
                for a in self.ambiguities
            ],
            "language": self.language,
            "complexity": self.complexity.value,
            "routing_hints": {
                "needs_general_model": self.routing_hints.needs_general_model,
                "needs_workspace_retrieval": self.routing_hints.needs_workspace_retrieval,
                "needs_structured_data": self.routing_hints.needs_structured_data,
                "needs_document_search": self.routing_hints.needs_document_search,
                "needs_conversation_search": self.routing_hints.needs_conversation_search,
                "needs_tool": self.routing_hints.needs_tool,
                "needs_clarification": self.routing_hints.needs_clarification,
            },
            "metadata": self.metadata,
        }
