from dataclasses import dataclass, field
from uuid import UUID, uuid4
from datetime import datetime
from typing import Dict, Any, Optional

@dataclass
class KnowledgeItem:
    """
    Normalized internal knowledge representation for MindMesh AI.
    Unifies documents, shared files, conversations, projects, decisions, and tasks
    under a consistent schema for ingestion, indexing, and retrieval.
    """
    id: UUID
    organization_id: UUID
    workspace_id: UUID
    source_type: str  # "document", "file", "conversation", "message", "project", "decision", "task"
    source_id: UUID
    source_name: str
    chunk_id: UUID
    content: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": str(self.id),
            "organization_id": str(self.organization_id),
            "workspace_id": str(self.workspace_id),
            "source_type": self.source_type,
            "source_id": str(self.source_id),
            "source_name": self.source_name,
            "chunk_id": str(self.chunk_id),
            "content": self.content,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
