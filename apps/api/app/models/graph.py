from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, Text, ForeignKey, Boolean, JSON, DateTime, Float, Index
from uuid import UUID, uuid4
from datetime import datetime
from typing import Optional, Dict, Any, List
from .base import BaseEntity

class GraphNode(BaseEntity):
    """Normalized representation of an entity node in the MindMesh Knowledge

    Graph.

    """
    __tablename__ = "graph_nodes"

    organization_id: Mapped[UUID] = mapped_column(ForeignKey("organizations.id", ondelete="CASCADE"), index=True, nullable=False)
    workspace_id: Mapped[Optional[UUID]] = mapped_column(ForeignKey("workspaces.id", ondelete="CASCADE"), index=True, nullable=True)
    project_id: Mapped[Optional[UUID]] = mapped_column(ForeignKey("projects.id", ondelete="SET NULL"), index=True, nullable=True)

    node_type: Mapped[str] = mapped_column(String(30), nullable=False, index=True)
    # ORGANIZATION, WORKSPACE, PROJECT, USER, DOCUMENT, FILE, CONVERSATION, MESSAGE, DECISION, TASK, FACT, TIMELINE_EVENT

    source_type: Mapped[str] = mapped_column(String(30), nullable=False, index=True)
    # document, file, message, conversation, project, task, decision, user, insight
    source_id: Mapped[UUID] = mapped_column(index=True, nullable=False)

    title: Mapped[str] = mapped_column(String(255), nullable=False)
    metadata_json: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)

    __table_args__ = (
        Index("idx_graph_node_source_unique", "source_type", "source_id", unique=True),
        Index("idx_graph_node_org_ws", "organization_id", "workspace_id"),
    )


class GraphEdge(BaseEntity):
    """Controlled, directional relationship edge linking two knowledge graph

    nodes.

    """
    __tablename__ = "graph_edges"

    organization_id: Mapped[UUID] = mapped_column(ForeignKey("organizations.id", ondelete="CASCADE"), index=True, nullable=False)
    workspace_id: Mapped[Optional[UUID]] = mapped_column(ForeignKey("workspaces.id", ondelete="CASCADE"), index=True, nullable=True)

    source_node_id: Mapped[UUID] = mapped_column(ForeignKey("graph_nodes.id", ondelete="CASCADE"), index=True, nullable=False)
    target_node_id: Mapped[UUID] = mapped_column(ForeignKey("graph_nodes.id", ondelete="CASCADE"), index=True, nullable=False)

    relation_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    # BELONGS_TO, CONTAINS, CREATED_BY, MEMBER_OF, PART_OF, RELATED_TO, MENTIONS, DERIVED_FROM, SUPPORTS,
    # DISCUSSED_IN, DECIDED_IN, ASSIGNED_TO, AFFECTS, RESULTED_IN, SUPERSEDES, UPDATED_BY, ATTACHED_TO, RELATED_TO_PROJECT

    evidence_type: Mapped[str] = mapped_column(String(30), nullable=False, default="EXPLICIT_FK")
    # EXPLICIT_FK, AI_DERIVED, TIMELINE_LINEAGE, SEMANTIC_INFERENCE

    confidence: Mapped[float] = mapped_column(Float, nullable=False, default=1.0)
    source_reference: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)

    source_node: Mapped["GraphNode"] = relationship("GraphNode", foreign_keys=[source_node_id])
    target_node: Mapped["GraphNode"] = relationship("GraphNode", foreign_keys=[target_node_id])

    __table_args__ = (
        Index("idx_graph_edge_unique", "source_node_id", "target_node_id", "relation_type", unique=True),
        Index("idx_graph_edge_org_ws", "organization_id", "workspace_id"),
    )
