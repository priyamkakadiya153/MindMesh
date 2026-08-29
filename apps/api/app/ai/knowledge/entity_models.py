import time
import uuid
from enum import Enum
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field

class EntityType(str, Enum):
    USER = "USER"
    PERSON = "PERSON"
    TEAM = "TEAM"
    ORGANIZATION = "ORGANIZATION"
    WORKSPACE = "WORKSPACE"
    PROJECT = "PROJECT"
    TASK = "TASK"
    DOCUMENT = "DOCUMENT"
    FILE = "FILE"
    CONVERSATION = "CONVERSATION"
    MESSAGE = "MESSAGE"
    MEETING = "MEETING"
    DECISION = "DECISION"
    KNOWLEDGE = "KNOWLEDGE"
    SYSTEM = "SYSTEM"
    SERVICE = "SERVICE"
    INTEGRATION = "INTEGRATION"
    EVENT = "EVENT"
    RISK = "RISK"
    WORKFLOW = "WORKFLOW"

class EntityStatus(str, Enum):
    ACTIVE = "ACTIVE"
    ARCHIVED = "ARCHIVED"
    DELETED = "DELETED"
    UNKNOWN = "UNKNOWN"

class ConfidenceLevel(str, Enum):
    VERIFIED = "VERIFIED"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    UNRESOLVED = "UNRESOLVED"

@dataclass
class CanonicalEntity:
    """Canonical Entity representation across MindMesh."""
    entity_id: uuid.UUID
    entity_type: EntityType
    canonical_name: str
    display_name: str
    aliases: List[str] = field(default_factory=list)
    identifiers: Dict[str, str] = field(default_factory=dict)  # e.g. {"jira": "PROJ-123", "db_id": "..."}
    scope: str = "WORKSPACE"
    owner_id: Optional[uuid.UUID] = None
    organization_id: Optional[uuid.UUID] = None
    workspace_id: Optional[uuid.UUID] = None
    status: EntityStatus = EntityStatus.ACTIVE
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "entity_id": str(self.entity_id),
            "entity_type": self.entity_type.value if hasattr(self.entity_type, "value") else str(self.entity_type),
            "canonical_name": self.canonical_name,
            "display_name": self.display_name,
            "aliases": self.aliases,
            "identifiers": self.identifiers,
            "scope": self.scope,
            "owner_id": str(self.owner_id) if self.owner_id else None,
            "organization_id": str(self.organization_id) if self.organization_id else None,
            "workspace_id": str(self.workspace_id) if self.workspace_id else None,
            "status": self.status.value if hasattr(self.status, "value") else str(self.status),
            "metadata": self.metadata
        }

@dataclass
class EntityAmbiguity:
    """Represents an ambiguous mention with tied candidate entities."""
    mention: str
    candidates: List[CanonicalEntity] = field(default_factory=list)
    reason: str = "MULTIPLE_EQUAL_MATCHES"
    confidence: ConfidenceLevel = ConfidenceLevel.UNRESOLVED
    clarification_prompt: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "mention": self.mention,
            "candidates": [c.to_dict() for c in self.candidates],
            "reason": self.reason,
            "confidence": self.confidence.value if hasattr(self.confidence, "value") else str(self.confidence),
            "clarification_prompt": self.clarification_prompt
        }
