import time
import uuid
from enum import Enum
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from app.ai.knowledge.entity_models import EntityType, ConfidenceLevel

class RelationshipType(str, Enum):
    OWNS = "OWNS"
    MEMBER_OF = "MEMBER_OF"
    ASSIGNED_TO = "ASSIGNED_TO"
    BELONGS_TO = "BELONGS_TO"
    CONTAINS = "CONTAINS"
    REFERENCES = "REFERENCES"
    MENTIONS = "MENTIONS"
    DEPENDS_ON = "DEPENDS_ON"
    BLOCKS = "BLOCKS"
    RELATED_TO = "RELATED_TO"
    DECIDED_BY = "DECIDED_BY"
    DERIVED_FROM = "DERIVED_FROM"
    CREATED_FROM = "CREATED_FROM"
    SUPPORTS = "SUPPORTS"
    CONTRADICTS = "CONTRADICTS"
    ATTACHED_TO = "ATTACHED_TO"
    PART_OF = "PART_OF"
    USES = "USES"
    CONNECTED_TO = "CONNECTED_TO"
    SUPERSEDES = "SUPERSEDES"

class EdgeStatus(str, Enum):
    ACTIVE = "ACTIVE"
    REVOKED = "REVOKED"
    SUPERSEDES = "SUPERSEDES"
    CONFLICTING = "CONFLICTING"

@dataclass
class GraphNode:
    """Knowledge Graph Node representation."""
    node_id: uuid.UUID
    entity_id: uuid.UUID
    entity_type: EntityType
    label: str
    scope: str = "WORKSPACE"
    workspace_id: Optional[uuid.UUID] = None
    organization_id: Optional[uuid.UUID] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "node_id": str(self.node_id),
            "entity_id": str(self.entity_id),
            "entity_type": self.entity_type.value if hasattr(self.entity_type, "value") else str(self.entity_type),
            "label": self.label,
            "scope": self.scope,
            "workspace_id": str(self.workspace_id) if self.workspace_id else None,
            "organization_id": str(self.organization_id) if self.organization_id else None,
            "metadata": self.metadata
        }

@dataclass
class GraphEdge:
    """Knowledge Graph Directional Edge representation."""
    edge_id: uuid.UUID
    source_entity_id: uuid.UUID
    target_entity_id: uuid.UUID
    relationship_type: RelationshipType
    confidence: ConfidenceLevel = ConfidenceLevel.HIGH
    provenance: str = "STRUCTURED_DB"
    valid_from: Optional[float] = field(default_factory=time.time)
    valid_until: Optional[float] = None
    workspace_id: Optional[uuid.UUID] = None
    organization_id: Optional[uuid.UUID] = None
    status: EdgeStatus = EdgeStatus.ACTIVE
    metadata: Dict[str, Any] = field(default_factory=dict)

    def is_currently_valid(self, current_timestamp: Optional[float] = None) -> bool:
        ts = current_timestamp or time.time()
        if self.status != EdgeStatus.ACTIVE:
            return False
        if self.valid_from and ts < self.valid_from:
            return False
        if self.valid_until and ts > self.valid_until:
            return False
        return True

    def to_dict(self) -> Dict[str, Any]:
        return {
            "edge_id": str(self.edge_id),
            "source_entity_id": str(self.source_entity_id),
            "target_entity_id": str(self.target_entity_id),
            "relationship_type": self.relationship_type.value if hasattr(self.relationship_type, "value") else str(self.relationship_type),
            "confidence": self.confidence.value if hasattr(self.confidence, "value") else str(self.confidence),
            "provenance": self.provenance,
            "valid_from": self.valid_from,
            "valid_until": self.valid_until,
            "workspace_id": str(self.workspace_id) if self.workspace_id else None,
            "organization_id": str(self.organization_id) if self.organization_id else None,
            "status": self.status.value if hasattr(self.status, "value") else str(self.status)
        }

@dataclass
class GraphConflict:
    """Represents conflicting edges in Knowledge Graph."""
    conflict_id: uuid.UUID
    entities: List[uuid.UUID]
    edges: List[GraphEdge]
    sources: List[str]
    status: str = "UNRESOLVED"
