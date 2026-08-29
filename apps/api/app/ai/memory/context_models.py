import time
import uuid
from enum import Enum
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field

class FactType(str, Enum):
    ENTITY_FACT = "ENTITY_FACT"
    DECISION_FACT = "DECISION_FACT"
    TASK_FACT = "TASK_FACT"
    PREFERENCE_FACT = "PREFERENCE_FACT"
    CONSTRAINT_FACT = "CONSTRAINT_FACT"

class FactStatus(str, Enum):
    OBSERVED = "OBSERVED"
    INFERRED = "INFERRED"
    USER_STATED = "USER_STATED"
    UNRESOLVED = "UNRESOLVED"
    CONFLICTING = "CONFLICTING"
    EXPIRED = "EXPIRED"

class TopicState(str, Enum):
    TOPIC_STARTED = "TOPIC_STARTED"
    TOPIC_CONTINUED = "TOPIC_CONTINUED"
    TOPIC_SHIFTED = "TOPIC_SHIFTED"
    TOPIC_RESUMED = "TOPIC_RESUMED"

@dataclass
class ConversationTopic:
    topic_label: str
    entities: List[str] = field(default_factory=list)
    scope: str = "WORKSPACE"
    confidence: str = "HIGH"
    state: TopicState = TopicState.TOPIC_STARTED
    last_updated: float = field(default_factory=time.time)

@dataclass
class ConversationFact:
    content: str
    fact_type: FactType = FactType.ENTITY_FACT
    fact_status: FactStatus = FactStatus.OBSERVED
    source_message_id: Optional[str] = None
    created_at: float = field(default_factory=time.time)

@dataclass
class ResolvedReference:
    reference_text: str
    resolved_entity: str
    confidence: str = "HIGH"
    source_context: Optional[str] = None

@dataclass
class ConversationContext:
    """Normalized Conversation Context Package Model."""
    conversation_id: uuid.UUID
    current_message_text: str
    recent_messages: List[Dict[str, Any]] = field(default_factory=list)
    summary: Optional[str] = None
    active_topics: List[ConversationTopic] = field(default_factory=list)
    entities: List[Dict[str, Any]] = field(default_factory=list)
    resolved_references: List[ResolvedReference] = field(default_factory=list)
    facts: List[ConversationFact] = field(default_factory=list)
    decisions: List[str] = field(default_factory=list)
    open_questions: List[str] = field(default_factory=list)
    user_preferences: Dict[str, str] = field(default_factory=dict)
    context_timestamp: float = field(default_factory=time.time)
    source_message_ids: List[str] = field(default_factory=list)
    version: int = 1
    confidence: str = "HIGH"
    context_prompt_text: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "conversation_id": str(self.conversation_id),
            "current_message_text": self.current_message_text,
            "recent_messages_count": len(self.recent_messages),
            "summary": self.summary,
            "active_topics": [t.topic_label for t in self.active_topics],
            "resolved_references": [
                {"reference_text": r.reference_text, "resolved_entity": r.resolved_entity}
                for r in self.resolved_references
            ],
            "facts": [{"content": f.content, "status": f.fact_status.value} for f in self.facts],
            "decisions": self.decisions,
            "open_questions": self.open_questions,
            "user_preferences": self.user_preferences,
            "version": self.version,
            "context_prompt_text": self.context_prompt_text
        }
