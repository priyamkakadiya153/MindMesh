import logging
from typing import List, Dict, Any, Optional, Set
from uuid import UUID
from datetime import datetime
from sqlalchemy import select, or_, and_
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.graph import GraphNode, GraphEdge
from ..models.user import User
from ..workspace.models import WorkspaceMember
from ..models.organization_member import OrganizationMember
from ..models.conversations import Conversation, ConversationMember
from ..models.chat import Chat

logger = logging.getLogger(__name__)

class KnowledgeGraphService:
    """Core service for managing GraphNode entities, establishing controlled

    GraphEdge relationships, and performing depth-controlled relationship

    queries with strict multi-tenant RBAC enforcement.

    """

    ALLOWED_RELATIONS: Set[str] = {
        "BELONGS_TO", "CONTAINS", "CREATED_BY", "MEMBER_OF", "PART_OF",
        "RELATED_TO", "MENTIONS", "DERIVED_FROM", "SUPPORTS", "DISCUSSED_IN",
        "DECIDED_IN", "ASSIGNED_TO", "AFFECTS", "RESULTED_IN", "SUPERSEDES",
        "UPDATED_BY", "ATTACHED_TO", "RELATED_TO_PROJECT"
    }

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_or_create_node(
        self,
        organization_id: UUID,
        node_type: str,
        source_type: str,
        source_id: UUID,
        title: str,
        workspace_id: Optional[UUID] = None,
        project_id: Optional[UUID] = None,
        metadata_json: Optional[Dict[str, Any]] = None
    ) -> GraphNode:
        """Idempotently creates or updates a GraphNode."""
        stmt = select(GraphNode).where(
            GraphNode.source_type == source_type,
            GraphNode.source_id == source_id
        )
        res = await self.db.execute(stmt)
        existing = res.scalars().first()

        if existing:
            existing.title = title
            existing.workspace_id = workspace_id or existing.workspace_id
            existing.project_id = project_id or existing.project_id
            existing.updated_at = datetime.utcnow()
            if metadata_json:
                merged = existing.metadata_json or {}
                merged.update(metadata_json)
                existing.metadata_json = merged
            await self.db.flush()
            return existing

        node = GraphNode(
            organization_id=organization_id,
            workspace_id=workspace_id,
            project_id=project_id,
            node_type=node_type.upper(),
            source_type=source_type,
            source_id=source_id,
            title=title,
            metadata_json=metadata_json or {}
        )
        self.db.add(node)
        await self.db.flush()
        return node

    async def create_edge(
        self,
        organization_id: UUID,
        source_node_id: UUID,
        target_node_id: UUID,
        relation_type: str,
        workspace_id: Optional[UUID] = None,
        evidence_type: str = "EXPLICIT_FK",
        confidence: float = 1.0,
        source_reference: Optional[Dict[str, Any]] = None
    ) -> Optional[GraphEdge]:
        """Idempotently creates a GraphEdge with a controlled relation_type."""
        rel_clean = relation_type.upper()
        if rel_clean not in self.ALLOWED_RELATIONS:
            rel_clean = "RELATED_TO"

        stmt = select(GraphEdge).where(
            GraphEdge.source_node_id == source_node_id,
            GraphEdge.target_node_id == target_node_id,
            GraphEdge.relation_type == rel_clean
        )
        res = await self.db.execute(stmt)
        existing = res.scalars().first()

        if existing:
            existing.confidence = max(existing.confidence, confidence)
            existing.updated_at = datetime.utcnow()
            if source_reference:
                merged_ref = existing.source_reference or {}
                merged_ref.update(source_reference)
                existing.source_reference = merged_ref
            await self.db.flush()
            return existing

        edge = GraphEdge(
            organization_id=organization_id,
            workspace_id=workspace_id,
            source_node_id=source_node_id,
            target_node_id=target_node_id,
            relation_type=rel_clean,
            evidence_type=evidence_type,
            confidence=confidence,
            source_reference=source_reference or {}
        )
        self.db.add(edge)
        await self.db.flush()
        return edge

    async def get_node_relationships(
        self,
        node_id: UUID,
        user: User,
        organization_id: UUID,
        depth: int = 1,
        limit: int = 40
    ) -> Dict[str, Any]:
        """Retrieves related nodes and edges up to requested depth (max 2) with

        full RBAC authorization enforcement.

        """
        depth = min(max(1, depth), 2)

        # 1. Org Authorization Check
        org_member_stmt = select(OrganizationMember.id).where(
            OrganizationMember.organization_id == organization_id,
            OrganizationMember.user_id == user.id
        )
        if not (await self.db.execute(org_member_stmt)).scalar_one_or_none():
            return {"center_node": None, "nodes": [], "edges": []}

        # 2. Accessible Workspaces & Chats
        user_ws_ids = await self._get_user_workspace_ids(user.id)
        auth_chat_ids = set(str(cid) for cid in (await self._get_authorized_chat_ids(user.id)))

        # Fetch center node
        center_stmt = select(GraphNode).where(
            GraphNode.id == node_id,
            GraphNode.organization_id == organization_id
        )
        center_node = (await self.db.execute(center_stmt)).scalar_one_or_none()
        if not center_node or not self._is_node_authorized(center_node, user_ws_ids, auth_chat_ids):
            return {"center_node": None, "nodes": [], "edges": []}

        visited_node_ids = {center_node.id}
        collected_nodes = [self._format_node(center_node)]
        collected_edges = []

        current_frontier = [center_node.id]

        for step in range(depth):
            if not current_frontier:
                break

            edge_stmt = select(GraphEdge).where(
                GraphEdge.organization_id == organization_id,
                or_(
                    GraphEdge.source_node_id.in_(current_frontier),
                    GraphEdge.target_node_id.in_(current_frontier)
                )
            ).limit(limit)
            edges_res = await self.db.execute(edge_stmt)
            step_edges = edges_res.scalars().all()

            next_frontier = []
            for edge in step_edges:
                other_id = edge.target_node_id if edge.source_node_id in current_frontier else edge.source_node_id

                # Fetch target node
                other_stmt = select(GraphNode).where(GraphNode.id == other_id)
                other_node = (await self.db.execute(other_stmt)).scalar_one_or_none()

                if other_node and self._is_node_authorized(other_node, user_ws_ids, auth_chat_ids):
                    if other_node.id not in visited_node_ids:
                        visited_node_ids.add(other_node.id)
                        collected_nodes.append(self._format_node(other_node))
                        next_frontier.append(other_node.id)

                    collected_edges.append({
                        "id": str(edge.id),
                        "source_node_id": str(edge.source_node_id),
                        "target_node_id": str(edge.target_node_id),
                        "relation_type": edge.relation_type,
                        "evidence_type": edge.evidence_type,
                        "confidence": edge.confidence,
                        "source_reference": edge.source_reference or {}
                    })

            current_frontier = next_frontier

        return {
            "center_node": self._format_node(center_node),
            "nodes": collected_nodes,
            "edges": collected_edges
        }

    async def search_nodes(
        self,
        user: User,
        organization_id: UUID,
        query: str,
        node_type: Optional[str] = None,
        workspace_id: Optional[UUID] = None,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        user_ws_ids = await self._get_user_workspace_ids(user.id)
        auth_chat_ids = set(str(cid) for cid in (await self._get_authorized_chat_ids(user.id)))

        conditions = [
            GraphNode.organization_id == organization_id,
            GraphNode.title.ilike(f"%{query.strip()}%")
        ]

        if node_type and node_type != "all":
            conditions.append(GraphNode.node_type == node_type.upper())

        if workspace_id:
            conditions.append(GraphNode.workspace_id == workspace_id)

        stmt = select(GraphNode).where(and_(*conditions)).limit(limit * 2)
        nodes = (await self.db.execute(stmt)).scalars().all()

        results = []
        for n in nodes:
            if self._is_node_authorized(n, user_ws_ids, auth_chat_ids):
                results.append(self._format_node(n))
                if len(results) >= limit:
                    break

        return results

    async def find_relationship_path(
        self,
        user_id: UUID,
        organization_id: UUID,
        source_id: UUID,
        target_id: UUID,
        max_depth: int = 4
    ) -> Optional[Dict[str, Any]]:
        """Finds multi-hop relationship paths between two graph nodes with human-readable explanations."""
        user_ws_ids = await self._get_user_workspace_ids(user_id)
        auth_chat_ids = await self._get_authorized_chat_ids(user_id)
        auth_chat_set = {str(cid) for cid in auth_chat_ids}

        # Fetch source and target nodes
        s_node = (await self.db.execute(select(GraphNode).where(GraphNode.id == source_id, GraphNode.organization_id == organization_id))).scalar_one_or_none()
        t_node = (await self.db.execute(select(GraphNode).where(GraphNode.id == target_id, GraphNode.organization_id == organization_id))).scalar_one_or_none()

        if not s_node or not t_node or not self._is_node_authorized(s_node, user_ws_ids, auth_chat_set) or not self._is_node_authorized(t_node, user_ws_ids, auth_chat_set):
            return None

        # BFS for multi-hop path
        queue = [[s_node.id]]
        visited = {s_node.id}
        node_map = {s_node.id: s_node, t_node.id: t_node}

        found_path_ids = None

        while queue:
            path = queue.pop(0)
            curr_id = path[-1]

            if curr_id == t_node.id:
                found_path_ids = path
                break

            if len(path) >= max_depth:
                continue

            edges_stmt = select(GraphEdge).where(
                or_(GraphEdge.source_node_id == curr_id, GraphEdge.target_node_id == curr_id),
                GraphEdge.organization_id == organization_id,
                GraphEdge.deleted_at.is_(None)
            )
            edges = (await self.db.execute(edges_stmt)).scalars().all()

            for edge in edges:
                next_id = edge.target_node_id if edge.source_node_id == curr_id else edge.source_node_id
                if next_id not in visited:
                    next_node = (await self.db.execute(select(GraphNode).where(GraphNode.id == next_id))).scalar_one_or_none()
                    if next_node and self._is_node_authorized(next_node, user_ws_ids, auth_chat_set):
                        visited.add(next_id)
                        node_map[next_id] = next_node
                        queue.append(path + [next_id])

        if not found_path_ids:
            return None

        path_nodes = [self._format_node(node_map[nid]) for nid in found_path_ids]
        explanation = f"Connected through {len(found_path_ids) - 1} relationship hops: " + " -> ".join([n["title"] for n in path_nodes])

        return {
            "path_nodes": path_nodes,
            "hop_count": len(found_path_ids) - 1,
            "explanation": explanation
        }

    async def get_relationship_suggestions(
        self,
        user_id: UUID,
        organization_id: UUID
    ) -> List[Dict[str, Any]]:
        """Surfaces AI-detected relationship candidates for human approval."""
        user_ws_ids = await self._get_user_workspace_ids(user_id)
        auth_chat_ids = await self._get_authorized_chat_ids(user_id)
        auth_chat_set = {str(cid) for cid in auth_chat_ids}

        stmt = select(GraphEdge).where(
            GraphEdge.organization_id == organization_id,
            GraphEdge.evidence_type != "EXPLICIT_FK",
            GraphEdge.deleted_at.is_(None)
        ).limit(20)

        edges = (await self.db.execute(stmt)).scalars().all()
        suggestions = []

        for e in edges:
            s_node = (await self.db.execute(select(GraphNode).where(GraphNode.id == e.source_node_id))).scalar_one_or_none()
            t_node = (await self.db.execute(select(GraphNode).where(GraphNode.id == e.target_node_id))).scalar_one_or_none()

            if s_node and t_node and self._is_node_authorized(s_node, user_ws_ids, auth_chat_set) and self._is_node_authorized(t_node, user_ws_ids, auth_chat_set):
                suggestions.append({
                    "edge_id": str(e.id),
                    "source_title": s_node.title,
                    "target_title": t_node.title,
                    "relation_type": e.relation_type,
                    "confidence": e.confidence,
                    "reason": e.source_reference.get("provenance_reason", "AI-detected semantic relationship") if e.source_reference else "AI-detected semantic relationship"
                })

        return suggestions

    async def accept_relationship_suggestion(
        self,
        edge_id: UUID,
        user_id: UUID,
        organization_id: UUID
    ) -> bool:
        """Approves an AI-detected relationship suggestion."""
        stmt = select(GraphEdge).where(GraphEdge.id == edge_id, GraphEdge.organization_id == organization_id)
        edge = (await self.db.execute(stmt)).scalar_one_or_none()
        if not edge:
            return False

        edge.evidence_type = "EXPLICIT_FK"
        edge.confidence = 1.0
        edge.updated_at = datetime.utcnow()
        await self.db.flush()
        return True

    async def reject_relationship_suggestion(
        self,
        edge_id: UUID,
        user_id: UUID,
        organization_id: UUID
    ) -> bool:
        """Rejects an AI-detected relationship suggestion."""
        stmt = select(GraphEdge).where(GraphEdge.id == edge_id, GraphEdge.organization_id == organization_id)
        edge = (await self.db.execute(stmt)).scalar_one_or_none()
        if not edge:
            return False

        edge.deleted_at = datetime.utcnow()
        await self.db.flush()
        return True

    def _is_node_authorized(self, node: GraphNode, user_ws_ids: List[UUID], auth_chat_set: Set[str]) -> bool:
        if node.workspace_id and node.workspace_id not in user_ws_ids:
            return False
        if node.source_type in ["message", "conversation"]:
            meta = node.metadata_json or {}
            chat_id = str(meta.get("chat_id") or node.source_id)
            if chat_id not in auth_chat_set:
                return False
        return True

    async def _get_user_workspace_ids(self, user_id: UUID) -> List[UUID]:
        stmt = select(WorkspaceMember.workspace_id).where(
            WorkspaceMember.user_id == user_id,
            WorkspaceMember.deleted_at.is_(None)
        )
        res = await self.db.execute(stmt)
        return [r[0] for r in res.all()]

    async def _get_authorized_chat_ids(self, user_id: UUID) -> List[UUID]:
        chat_ids = set()
        stmt1 = select(Chat.id).where(Chat.user_id == user_id, Chat.deleted_at.is_(None))
        res1 = await self.db.execute(stmt1)
        for r in res1.scalars().all():
            chat_ids.add(r)

        stmt2 = select(Conversation.id).where(
            or_(
                Conversation.participant_one == user_id,
                Conversation.participant_two == user_id,
                Conversation.id.in_(
                    select(ConversationMember.conversation_id).where(
                        ConversationMember.user_id == user_id,
                        ConversationMember.deleted_at.is_(None)
                    )
                )
            ),
            Conversation.deleted_at.is_(None)
        )
        res2 = await self.db.execute(stmt2)
        for r in res2.scalars().all():
            chat_ids.add(r)

        return list(chat_ids)

    def _format_node(self, node: GraphNode) -> Dict[str, Any]:
        meta = node.metadata_json or {}
        deep_link = meta.get("deep_link") or self._build_deep_link(node.source_type, str(node.source_id), meta)
        return {
            "id": str(node.id),
            "organization_id": str(node.organization_id),
            "workspace_id": str(node.workspace_id) if node.workspace_id else None,
            "project_id": str(node.project_id) if node.project_id else None,
            "node_type": node.node_type,
            "source_type": node.source_type,
            "source_id": str(node.source_id),
            "title": node.title,
            "metadata": meta,
            "deep_link": deep_link
        }

    def _build_deep_link(self, source_type: str, source_id: str, metadata: Dict[str, Any]) -> str:
        if source_type in ["document", "file"]:
            return f"/files?preview={source_id}"
        elif source_type in ["message", "conversation"]:
            chat_id = metadata.get("chat_id") or source_id
            msg_id = metadata.get("message_id") or source_id
            return f"/direct-messages?chat={chat_id}&msg={msg_id}"
        elif source_type == "project":
            return f"/projects/{source_id}"
        elif source_type == "task":
            return f"/tasks/{source_id}"
        elif source_type == "decision":
            return f"/decisions/{source_id}"
        else:
            return "/dashboard"
