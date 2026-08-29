import time
import uuid
import logging
from collections import deque
from typing import List, Dict, Any, Optional, Set, Tuple

from app.ai.knowledge.graph_models import (
    GraphNode,
    GraphEdge,
    RelationshipType,
    EdgeStatus,
    GraphConflict
)
from app.ai.knowledge.entity_models import CanonicalEntity, EntityType, ConfidenceLevel

logger = logging.getLogger(__name__)

class KnowledgeGraphService:
    """
    Knowledge Graph Query & Management Service.
    
    Responsibilities:
    - Node & directional Edge creation & lookup
    - Multi-tenant security boundary enforcement (Workspace & Organization filters)
    - Neighbor lookup (1-hop, 2-hop)
    - Path discovery (find_path) with circular cycle detection & recursion depth bounds
    - Conflict detection & resolution
    """

    _instance: Optional["KnowledgeGraphService"] = None

    def __init__(self):
        self._nodes: Dict[uuid.UUID, GraphNode] = {}                      # entity_id -> GraphNode
        self._edges_outgoing: Dict[uuid.UUID, List[GraphEdge]] = {}       # source_entity_id -> List[GraphEdge]
        self._edges_incoming: Dict[uuid.UUID, List[GraphEdge]] = {}       # target_entity_id -> List[GraphEdge]

    @classmethod
    def get_instance(cls) -> "KnowledgeGraphService":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def add_node(self, entity: CanonicalEntity) -> GraphNode:
        node = GraphNode(
            node_id=uuid.uuid4(),
            entity_id=entity.entity_id,
            entity_type=entity.entity_type,
            label=entity.display_name,
            scope=entity.scope,
            workspace_id=entity.workspace_id,
            organization_id=entity.organization_id
        )
        self._nodes[entity.entity_id] = node
        return node

    def add_edge(
        self,
        source_id: uuid.UUID,
        target_id: uuid.UUID,
        rel_type: RelationshipType,
        confidence: ConfidenceLevel = ConfidenceLevel.HIGH,
        provenance: str = "STRUCTURED_DB",
        workspace_id: Optional[uuid.UUID] = None,
        organization_id: Optional[uuid.UUID] = None
    ) -> GraphEdge:
        edge = GraphEdge(
            edge_id=uuid.uuid4(),
            source_entity_id=source_id,
            target_entity_id=target_id,
            relationship_type=rel_type,
            confidence=confidence,
            provenance=provenance,
            workspace_id=workspace_id,
            organization_id=organization_id,
            status=EdgeStatus.ACTIVE
        )

        if source_id not in self._edges_outgoing:
            self._edges_outgoing[source_id] = []
        self._edges_outgoing[source_id].append(edge)

        if target_id not in self._edges_incoming:
            self._edges_incoming[target_id] = []
        self._edges_incoming[target_id].append(edge)

        return edge

    def get_neighbors(
        self,
        entity_id: uuid.UUID,
        max_depth: int = 1,
        organization_id: Optional[uuid.UUID] = None,
        workspace_id: Optional[uuid.UUID] = None
    ) -> List[GraphNode]:
        if entity_id not in self._nodes:
            return []

        visited: Set[uuid.UUID] = {entity_id}
        queue: deque = deque([(entity_id, 0)])
        result_nodes: List[GraphNode] = []

        while queue:
            curr_id, depth = queue.popleft()
            if depth >= max_depth:
                continue

            # Outgoing & Incoming edges
            out_edges = self._edges_outgoing.get(curr_id, [])
            in_edges = self._edges_incoming.get(curr_id, [])
            all_edges = out_edges + in_edges

            for edge in all_edges:
                if not edge.is_currently_valid():
                    continue

                # Permission filter
                if organization_id and edge.organization_id and edge.organization_id != organization_id:
                    continue
                if workspace_id and edge.workspace_id and edge.workspace_id != workspace_id:
                    continue

                nbr_id = edge.target_entity_id if edge.source_entity_id == curr_id else edge.source_entity_id
                if nbr_id not in visited:
                    visited.add(nbr_id)
                    if nbr_id in self._nodes:
                        result_nodes.append(self._nodes[nbr_id])
                        queue.append((nbr_id, depth + 1))

        return result_nodes

    def get_relationships(
        self,
        entity_id: uuid.UUID,
        rel_type: Optional[RelationshipType] = None,
        organization_id: Optional[uuid.UUID] = None,
        workspace_id: Optional[uuid.UUID] = None
    ) -> List[GraphEdge]:
        out_edges = self._edges_outgoing.get(entity_id, [])
        in_edges = self._edges_incoming.get(entity_id, [])
        all_edges = [e for e in (out_edges + in_edges) if e.is_currently_valid()]

        if rel_type:
            all_edges = [e for e in all_edges if e.relationship_type == rel_type]

        if organization_id:
            all_edges = [e for e in all_edges if not e.organization_id or e.organization_id == organization_id]
        if workspace_id:
            all_edges = [e for e in all_edges if not e.workspace_id or e.workspace_id == workspace_id]

        return all_edges

    def find_path(
        self,
        source_id: uuid.UUID,
        target_id: uuid.UUID,
        max_hops: int = 3,
        organization_id: Optional[uuid.UUID] = None,
        workspace_id: Optional[uuid.UUID] = None
    ) -> List[GraphEdge]:
        """BFS Path Search with Cycle Protection & Hard Recursion Bounds."""
        if source_id == target_id:
            return []

        visited: Set[uuid.UUID] = {source_id}
        queue: deque = deque([(source_id, [])])

        while queue:
            curr_id, path = queue.popleft()
            if len(path) >= max_hops:
                continue

            out_edges = self._edges_outgoing.get(curr_id, [])
            for edge in out_edges:
                if not edge.is_currently_valid():
                    continue

                if organization_id and edge.organization_id and edge.organization_id != organization_id:
                    continue
                if workspace_id and edge.workspace_id and edge.workspace_id != workspace_id:
                    continue

                nxt = edge.target_entity_id
                if nxt == target_id:
                    return path + [edge]

                if nxt not in visited:
                    visited.add(nxt)
                    queue.append((nxt, path + [edge]))

        return []
