import logging
from typing import List, Dict, Any, Optional, Set
from uuid import UUID
from datetime import datetime
from sqlalchemy import select, or_, and_, desc
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.graph import GraphNode, GraphEdge
from ..models.user import User
from ..models.organization import Organization
from ..workspace.models import Workspace
from ..projects.models import Project
from ..documents.models import Document
from ..models.task import Task
from ..models.conversation import ConversationMemory
from ..models.conversations import Conversation, DirectMessage
from ..models.timeline import TimelineEvent, TimelineRelation
from ..models.audit import AuditLog

logger = logging.getLogger(__name__)

RELATION_DISPLAY_MAP = {
    "BELONGS_TO": "Belongs to",
    "CONTAINS": "Contains",
    "CREATED_BY": "Created by",
    "MEMBER_OF": "Member of",
    "PART_OF": "Part of",
    "RELATED_TO": "Related to",
    "MENTIONS": "Mentions",
    "DERIVED_FROM": "Created from",
    "SUPPORTS": "Supports",
    "DISCUSSED_IN": "Discussed in",
    "DECIDED_IN": "Decided in",
    "ASSIGNED_TO": "Owned by",
    "AFFECTS": "Affects",
    "RESULTED_IN": "Led to",
    "SUPERSEDES": "Supersedes",
    "UPDATED_BY": "Changed by",
    "ATTACHED_TO": "Attached to",
    "RELATED_TO_PROJECT": "Related to project",
    "DEPENDS_ON": "Depends on",
    "BLOCKED_BY": "Blocked by"
}

class ConnectionsService:
    """
    Proven Cross-Entity Relationship Intelligence Service for MindMesh.
    Answers core relationship questions (Why exists, Cause/Effect, Provenance Chains, Dependencies)
    using authentic database records with zero synthetic/demo data.
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_relationship_overview(
        self,
        user: User,
        organization_id: UUID,
        workspace_id: Optional[UUID] = None
    ) -> Dict[str, Any]:
        """Retrieves verified relationship summaries across the workspace."""
        # 1. Fetch blocked tasks
        task_stmt = select(Task).where(
            Task.organization_id == organization_id,
            Task.deleted_at.is_(None),
            Task.status == "blocked"
        )
        if workspace_id:
            task_stmt = task_stmt.outerjoin(Project, Task.project_id == Project.id).where(
                or_(Task.workspace_id == workspace_id, Project.workspace_id == workspace_id)
            )
        blocked_tasks = (await self.db.execute(task_stmt.limit(10))).scalars().all()

        blocked_work_items = []
        for t in blocked_tasks:
            blocked_work_items.append({
                "entity_id": str(t.id),
                "entity_type": "TASK",
                "title": t.description or t.title or "Untitled Task",
                "status": t.status,
                "project_id": str(t.project_id) if t.project_id else None,
                "reason": "Task is marked as blocked in workspace records.",
                "human_relation": "Blocked by"
            })

        # 2. Fetch recent decisions (from ConversationMemory)
        mem_stmt = select(ConversationMemory).where(
            ConversationMemory.organization_id == organization_id,
            ConversationMemory.deleted_at.is_(None),
            ConversationMemory.memory_type == "decision"
        ).order_by(desc(ConversationMemory.created_at)).limit(10)

        recent_decisions_raw = (await self.db.execute(mem_stmt)).scalars().all()
        recent_decisions = []
        for d in recent_decisions_raw:
            recent_decisions.append({
                "entity_id": str(d.id),
                "entity_type": "DECISION",
                "title": d.content[:120],
                "created_at": d.created_at.isoformat() if d.created_at else None,
                "human_relation": "Led to"
            })

        # 3. Fetch verified graph edge connections
        edge_stmt = select(GraphEdge).where(
            GraphEdge.organization_id == organization_id
        ).order_by(desc(GraphEdge.confidence), desc(GraphEdge.created_at)).limit(20)
        
        edges = (await self.db.execute(edge_stmt)).scalars().all()
        important_connections = []
        for e in edges:
            src_node = (await self.db.execute(select(GraphNode).where(GraphNode.id == e.source_node_id))).scalar_one_or_none()
            tgt_node = (await self.db.execute(select(GraphNode).where(GraphNode.id == e.target_node_id))).scalar_one_or_none()
            if src_node and tgt_node:
                important_connections.append({
                    "edge_id": str(e.id),
                    "source_id": str(src_node.source_id),
                    "source_type": src_node.node_type,
                    "source_title": src_node.title,
                    "target_id": str(tgt_node.source_id),
                    "target_type": tgt_node.node_type,
                    "target_title": tgt_node.title,
                    "relation_type": e.relation_type,
                    "human_relation": RELATION_DISPLAY_MAP.get(e.relation_type, e.relation_type),
                    "evidence_type": e.evidence_type,
                    "confidence": e.confidence
                })

        return {
            "has_connections": len(important_connections) > 0 or len(blocked_work_items) > 0 or len(recent_decisions) > 0,
            "blocked_work": blocked_work_items,
            "recent_decisions": recent_decisions,
            "important_connections": important_connections
        }

    async def get_entity_provenance(
        self,
        entity_type: str,
        entity_id: UUID,
        user: User,
        organization_id: UUID
    ) -> Dict[str, Any]:
        """
        Assembles 360° Human-Centered Relationship Inspector Data.
        Answers:
        - Why it exists
        - Connected Project
        - Supporting Evidence
        - Related Decisions
        - Resulting Tasks
        - Dependencies & Blockers
        - Current Impact
        - Step-by-Step Provenance Chain
        - Grouped Connected Entities
        """
        e_type_upper = entity_type.upper()

        # 1. Locate GraphNode if present
        node_stmt = select(GraphNode).where(
            GraphNode.organization_id == organization_id,
            GraphNode.source_id == entity_id
        )
        node = (await self.db.execute(node_stmt)).scalar_one_or_none()

        entity_title = f"{e_type_upper} {str(entity_id)[:8]}"
        deep_link = None
        status = None
        owner = None
        project_name = None
        created_at_str = None
        metadata = {}

        # 2. Fetch specific entity DB model
        if e_type_upper == "TASK":
            task = (await self.db.execute(select(Task).where(Task.id == entity_id))).scalar_one_or_none()
            if task:
                entity_title = task.title or task.description
                status = task.status
                deep_link = f"/tasks/{task.id}"
                created_at_str = task.created_at.isoformat() if task.created_at else None
                if task.project_id:
                    proj = (await self.db.execute(select(Project).where(Project.id == task.project_id))).scalar_one_or_none()
                    if proj:
                        project_name = proj.name

        elif e_type_upper == "PROJECT":
            proj = (await self.db.execute(select(Project).where(Project.id == entity_id))).scalar_one_or_none()
            if proj:
                entity_title = proj.name
                status = proj.status
                deep_link = f"/projects/{proj.id}"
                created_at_str = proj.created_at.isoformat() if proj.created_at else None

        elif e_type_upper == "DOCUMENT":
            doc = (await self.db.execute(select(Document).where(Document.id == entity_id))).scalar_one_or_none()
            if doc:
                entity_title = doc.title
                metadata["filename"] = doc.filename
                metadata["mime_type"] = doc.mime_type
                deep_link = f"/files?preview={doc.id}"
                created_at_str = doc.created_at.isoformat() if doc.created_at else None

        elif e_type_upper == "DECISION":
            mem = (await self.db.execute(select(ConversationMemory).where(ConversationMemory.id == entity_id))).scalar_one_or_none()
            if mem:
                entity_title = mem.content
                metadata["memory_type"] = mem.memory_type
                created_at_str = mem.created_at.isoformat() if mem.created_at else None

        # 3. Categorized Relationship Collections
        why_exists: Optional[str] = None
        connected_project: Optional[Dict[str, Any]] = None
        supporting_evidence: List[Dict[str, Any]] = []
        related_decisions: List[Dict[str, Any]] = []
        resulting_tasks: List[Dict[str, Any]] = []
        dependencies_and_blockers: List[Dict[str, Any]] = []
        current_impact: List[Dict[str, Any]] = []
        provenance_trail: List[Dict[str, Any]] = []
        
        # Grouped connected entities for bottom section
        grouped_entities: Dict[str, List[Dict[str, Any]]] = {
            "DECISIONS": [],
            "TASKS": [],
            "CONVERSATIONS": [],
            "DOCUMENTS": [],
            "PEOPLE": []
        }

        has_verified_edges = False

        if node:
            # Outgoing edges (Source = Node)
            out_edges = (await self.db.execute(select(GraphEdge).where(GraphEdge.source_node_id == node.id))).scalars().all()
            for edge in out_edges:
                tgt = (await self.db.execute(select(GraphNode).where(GraphNode.id == edge.target_node_id))).scalar_one_or_none()
                if tgt:
                    has_verified_edges = True
                    item_data = {
                        "id": str(tgt.source_id),
                        "node_id": str(tgt.id),
                        "type": tgt.node_type,
                        "title": tgt.title,
                        "relation": RELATION_DISPLAY_MAP.get(edge.relation_type, edge.relation_type),
                        "confidence": edge.confidence,
                        "evidence_type": edge.evidence_type,
                        "deep_link": tgt.metadata_json.get("deep_link") if tgt.metadata_json else None
                    }

                    # Populate structured sections
                    if edge.relation_type in ["RESULTED_IN", "CONTAINS"]:
                        resulting_tasks.append(item_data)
                    elif edge.relation_type in ["SUPPORTS"]:
                        supporting_evidence.append(item_data)
                    elif edge.relation_type in ["DECIDED_IN"]:
                        related_decisions.append(item_data)
                    elif edge.relation_type in ["DEPENDS_ON", "BLOCKED_BY"]:
                        dependencies_and_blockers.append(item_data)
                    elif edge.relation_type in ["AFFECTS"]:
                        current_impact.append(item_data)

                    # Populate grouped categories
                    t_group = "DOCUMENTS" if tgt.node_type in ["DOCUMENT", "FILE"] else (
                        "TASKS" if tgt.node_type == "TASK" else (
                            "DECISIONS" if tgt.node_type == "DECISION" else (
                                "CONVERSATIONS" if tgt.node_type in ["CONVERSATION", "MESSAGE"] else "PEOPLE"
                            )
                        )
                    )
                    grouped_entities[t_group].append(item_data)

            # Incoming edges (Target = Node)
            in_edges = (await self.db.execute(select(GraphEdge).where(GraphEdge.target_node_id == node.id))).scalars().all()
            for edge in in_edges:
                src = (await self.db.execute(select(GraphNode).where(GraphNode.id == edge.source_node_id))).scalar_one_or_none()
                if src:
                    has_verified_edges = True
                    item_data = {
                        "id": str(src.source_id),
                        "node_id": str(src.id),
                        "type": src.node_type,
                        "title": src.title,
                        "relation": RELATION_DISPLAY_MAP.get(edge.relation_type, edge.relation_type),
                        "confidence": edge.confidence,
                        "evidence_type": edge.evidence_type,
                        "deep_link": src.metadata_json.get("deep_link") if src.metadata_json else None
                    }

                    if edge.relation_type in ["SUPPORTS"]:
                        supporting_evidence.append(item_data)
                    elif edge.relation_type in ["DERIVED_FROM", "CREATED_BY"]:
                        why_exists = f"Created from {src.title}"
                        provenance_trail.append(item_data)
                    elif edge.relation_type in ["CONTAINS"] and src.node_type == "PROJECT":
                        connected_project = item_data
                    elif edge.relation_type in ["DECIDED_IN"]:
                        related_decisions.append(item_data)

                    s_group = "DOCUMENTS" if src.node_type in ["DOCUMENT", "FILE"] else (
                        "TASKS" if src.node_type == "TASK" else (
                            "DECISIONS" if src.node_type == "DECISION" else (
                                "CONVERSATIONS" if src.node_type in ["CONVERSATION", "MESSAGE"] else "PEOPLE"
                            )
                        )
                    )
                    grouped_entities[s_group].append(item_data)

        # 4. Fallback implicit FK connections if graph edges not fully indexed
        if not connected_project and project_name:
            connected_project = {
                "id": str(entity_id),
                "type": "PROJECT",
                "title": project_name,
                "relation": "Belongs to project",
                "confidence": 1.0,
                "evidence_type": "EXPLICIT_FK"
            }

        # 5. Build step-by-step Provenance Chain Array (e.g. Document -> Decision -> Task -> Project)
        provenance_chain = []
        provenance_chain.append({"type": e_type_upper, "id": str(entity_id), "title": entity_title})
        if supporting_evidence:
            provenance_chain.insert(0, {"type": supporting_evidence[0]["type"], "id": supporting_evidence[0]["id"], "title": supporting_evidence[0]["title"]})
        if resulting_tasks and e_type_upper != "TASK":
            provenance_chain.append({"type": resulting_tasks[0]["type"], "id": resulting_tasks[0]["id"], "title": resulting_tasks[0]["title"]})
        if connected_project and e_type_upper != "PROJECT":
            provenance_chain.append({"type": "PROJECT", "id": connected_project.get("id", ""), "title": connected_project["title"]})

        return {
            "entity_id": str(entity_id),
            "entity_type": e_type_upper,
            "title": entity_title,
            "status": status,
            "owner": owner,
            "created_at": created_at_str,
            "deep_link": deep_link,
            "metadata": metadata,
            "has_verified_connections": has_verified_edges or (connected_project is not None),
            "why_exists": why_exists,
            "connected_project": connected_project,
            "supporting_evidence": supporting_evidence,
            "related_decisions": related_decisions,
            "resulting_tasks": resulting_tasks,
            "dependencies_and_blockers": dependencies_and_blockers,
            "current_impact": current_impact,
            "provenance_trail": provenance_trail,
            "provenance_chain": provenance_chain,
            "grouped_entities": grouped_entities
        }
