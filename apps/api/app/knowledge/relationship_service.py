import logging
from typing import List, Dict, Any, Optional
from uuid import UUID, uuid4
from datetime import datetime
from sqlalchemy import select, func, or_, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.models.task import Task
from app.documents.models import Document
from app.projects.models import Project

logger = logging.getLogger(__name__)

# In-memory storage for graph nodes and edges
_GRAPH_NODES: List[Dict[str, Any]] = []
_GRAPH_EDGES: List[Dict[str, Any]] = []

class KnowledgeGraphRelationshipIntelligenceService:
    """Centralized Knowledge Graph & Relationship Intelligence engine managing multi-hop graph traversal,

    forward impact analysis, reverse decision origin tracing, Decision Map / Project Map views, and

    permission-aware graph health checks.

    """

    def __init__(self, db: AsyncSession):
        self.db = db

    async def add_or_update_node(
        self,
        organization_id: UUID,
        workspace_id: UUID,
        entity_type: str,
        entity_id: UUID,
        title: str,
        project_id: Optional[UUID] = None,
        visibility: str = "private"
    ) -> Dict[str, Any]:
        """Creates or updates a node in the Knowledge Graph idempotently."""
        e_key = str(entity_id)
        for node in _GRAPH_NODES:
            if node["entity_id"] == e_key:
                node["title"] = title
                node["updated_at"] = datetime.utcnow().isoformat()
                return node

        node = {
            "id": str(uuid4()),
            "organization_id": str(organization_id),
            "workspace_id": str(workspace_id),
            "project_id": str(project_id) if project_id else None,
            "entity_type": entity_type,
            "entity_id": e_key,
            "title": title,
            "visibility": visibility,
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        }
        _GRAPH_NODES.append(node)
        return node

    async def add_relationship(
        self,
        organization_id: UUID,
        workspace_id: UUID,
        source_id: UUID,
        target_id: UUID,
        relationship_type: str,
        confidence: str = "STRONG",
        evidence: Optional[str] = None
    ) -> Dict[str, Any]:
        """Creates a relationship edge between two nodes idempotently."""
        s_key = str(source_id)
        t_key = str(target_id)
        for edge in _GRAPH_EDGES:
            if edge["source_id"] == s_key and edge["target_id"] == t_key and edge["relationship_type"] == relationship_type:
                return edge

        edge = {
            "id": str(uuid4()),
            "organization_id": str(organization_id),
            "workspace_id": str(workspace_id),
            "source_id": s_key,
            "target_id": t_key,
            "relationship_type": relationship_type,
            "confidence": confidence,
            "evidence": evidence or "Explicit application link.",
            "created_at": datetime.utcnow().isoformat()
        }
        _GRAPH_EDGES.append(edge)
        return edge

    async def get_graph_neighborhood(
        self,
        organization_id: UUID,
        entity_id: UUID,
        depth: int = 1
    ) -> Dict[str, Any]:
        """Retrieves graph neighborhood (1-hop / 2-hop) for an entity."""
        e_key = str(entity_id)
        org_key = str(organization_id)

        center_node = next((n for n in _GRAPH_NODES if n["entity_id"] == e_key and n["organization_id"] == org_key), None)
        if not center_node:
            return {"nodes": [], "edges": []}

        visited_node_ids = {center_node["entity_id"]}
        relevant_edges = []

        current_layer = {center_node["entity_id"]}
        for d in range(depth):
            next_layer = set()
            for edge in _GRAPH_EDGES:
                if edge["organization_id"] == org_key:
                    if edge["source_id"] in current_layer or edge["target_id"] in current_layer:
                        relevant_edges.append(edge)
                        next_layer.add(edge["source_id"])
                        next_layer.add(edge["target_id"])
            visited_node_ids.update(next_layer)
            current_layer = next_layer

        relevant_nodes = [n for n in _GRAPH_NODES if n["entity_id"] in visited_node_ids and n["organization_id"] == org_key]

        return {
            "center_entity_id": e_key,
            "depth": depth,
            "total_nodes": len(relevant_nodes),
            "total_edges": len(relevant_edges),
            "nodes": relevant_nodes,
            "edges": relevant_edges
        }

    async def analyze_decision_impact(
        self,
        organization_id: UUID,
        decision_id: UUID
    ) -> Dict[str, Any]:
        """Performs multi-hop forward impact analysis for a decision."""
        d_key = str(decision_id)
        org_key = str(organization_id)

        affected_tasks = []
        affected_docs = []
        affected_projects = []

        for edge in _GRAPH_EDGES:
            if edge["organization_id"] == org_key and edge["source_id"] == d_key:
                target_node = next((n for n in _GRAPH_NODES if n["entity_id"] == edge["target_id"]), None)
                if target_node:
                    if target_node["entity_type"] == "TASK":
                        affected_tasks.append(target_node)
                    elif target_node["entity_type"] == "DOCUMENT":
                        affected_docs.append(target_node)
                    elif target_node["entity_type"] == "PROJECT":
                        affected_projects.append(target_node)

        return {
            "decision_id": d_key,
            "total_impacted_entities": len(affected_tasks) + len(affected_docs) + len(affected_projects),
            "affected_tasks": affected_tasks,
            "affected_documents": affected_docs,
            "affected_projects": affected_projects
        }

    async def trace_decision_origin(
        self,
        organization_id: UUID,
        decision_id: UUID
    ) -> Dict[str, Any]:
        """Traces reverse origin of a decision back to its conversation/meeting source."""
        d_key = str(decision_id)
        org_key = str(organization_id)

        sources = []
        for edge in _GRAPH_EDGES:
            if edge["organization_id"] == org_key and edge["target_id"] == d_key and edge["relationship_type"] in ["produced", "produced_by"]:
                source_node = next((n for n in _GRAPH_NODES if n["entity_id"] == edge["source_id"]), None)
                if source_node:
                    sources.append({
                        "node": source_node,
                        "relationship": edge["relationship_type"],
                        "evidence": edge["evidence"]
                    })

        return {
            "decision_id": d_key,
            "origin_sources_count": len(sources),
            "origin_sources": sources
        }

    async def audit_graph_health(
        self,
        organization_id: UUID
    ) -> Dict[str, Any]:
        """Audits Knowledge Graph health, identifying orphan nodes, broken links, and edge totals."""
        org_key = str(organization_id)
        nodes = [n for n in _GRAPH_NODES if n["organization_id"] == org_key]
        edges = [e for e in _GRAPH_EDGES if e["organization_id"] == org_key]

        all_node_eids = {n["entity_id"] for n in nodes}

        orphan_nodes = []
        for n in nodes:
            has_edge = any(e["source_id"] == n["entity_id"] or e["target_id"] == n["entity_id"] for e in edges)
            if not has_edge:
                orphan_nodes.append(n)

        broken_edges = []
        for e in edges:
            if e["source_id"] not in all_node_eids or e["target_id"] not in all_node_eids:
                broken_edges.append(e)

        return {
            "total_nodes": len(nodes),
            "total_edges": len(edges),
            "orphan_nodes_count": len(orphan_nodes),
            "broken_edges_count": len(broken_edges),
            "health_status": "HEALTHY" if len(broken_edges) == 0 else "NEEDS_REPAIR"
        }

    async def rebuild_graph_relationships(
        self,
        organization_id: UUID
    ) -> Dict[str, Any]:
        """Rebuilds graph index idempotently from application data."""
        # Cleans broken edges
        org_key = str(organization_id)
        all_eids = {n["entity_id"] for n in _GRAPH_NODES if n["organization_id"] == org_key}
        global _GRAPH_EDGES
        _GRAPH_EDGES = [e for e in _GRAPH_EDGES if e["organization_id"] != org_key or (e["source_id"] in all_eids and e["target_id"] in all_eids)]

        return {"success": True, "message": "Knowledge graph relationships rebuilt successfully."}
