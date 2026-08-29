import logging
from typing import List, Dict, Any, Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession

from .graph_service import KnowledgeGraphService
from ..search.query_processor import QueryProcessor
from ..models.graph import GraphNode, GraphEdge
from ..models.user import User

logger = logging.getLogger(__name__)

class GraphRetriever:
    """Retrieves connected knowledge entities and relationship triples for MindMesh

    AI Orchestrator prompt context expansion.

    """

    def __init__(self, db: AsyncSession):
        self.db = db
        self.service = KnowledgeGraphService(db)

    async def expand_context(
        self,
        user: User,
        organization_id: UUID,
        query_text: str,
        workspace_id: Optional[UUID] = None,
        top_nodes: int = 5
    ) -> Dict[str, Any]:
        qp = QueryProcessor.process(query_text)
        keywords = qp["important_keywords"]

        matching_nodes: List[Dict[str, Any]] = []
        seen_node_ids = set()

        # 1. Search nodes using processed keywords
        for kw in (keywords or [query_text]):
            if len(kw) < 2:
                continue
            nodes_kw = await self.service.search_nodes(
                user=user,
                organization_id=organization_id,
                query=kw,
                workspace_id=workspace_id,
                limit=top_nodes
            )
            for n in nodes_kw:
                if n["id"] not in seen_node_ids:
                    seen_node_ids.add(n["id"])
                    matching_nodes.append(n)
                if len(matching_nodes) >= top_nodes * 2:
                    break

        entities = []
        relationships = []
        seen_edge_ids = set()

        for node_dict in matching_nodes[:top_nodes]:
            if not any(e["id"] == node_dict["id"] for e in entities):
                entities.append(node_dict)

            rel_data = await self.service.get_node_relationships(
                node_id=UUID(node_dict["id"]),
                user=user,
                organization_id=organization_id,
                depth=1,
                limit=15
            )

            for n in rel_data.get("nodes", []):
                if not any(e["id"] == n["id"] for e in entities):
                    entities.append(n)

            for edge in rel_data.get("edges", []):
                if edge["id"] not in seen_edge_ids:
                    seen_edge_ids.add(edge["id"])
                    src_n = next((e for e in entities if e["id"] == edge["source_node_id"]), None)
                    tgt_n = next((e for e in entities if e["id"] == edge["target_node_id"]), None)

                    if src_n and tgt_n:
                        relationships.append({
                            "source_title": src_n["title"],
                            "source_type": src_n["node_type"],
                            "relation_type": edge["relation_type"],
                            "target_title": tgt_n["title"],
                            "target_type": tgt_n["node_type"],
                            "confidence": edge["confidence"]
                        })

        return {
            "entities": entities[:20],
            "relationships": relationships[:30]
        }
