import logging
from typing import List, Dict, Any, Optional
from uuid import UUID

from app.ai.retrieval.models import EvidenceSet, EvidenceItem
from app.ai.knowledge.entity_resolution import EntityResolutionEngine, EntityRegistry
from app.ai.knowledge.graph_service import KnowledgeGraphService

logger = logging.getLogger(__name__)

class EntityAwareRetrievalBridge:
    """
    Entity-Aware Retrieval Bridge.
    Links AI-05 Evidence items to canonical graph entities and injects graph connection signals.
    """

    @classmethod
    def enrich_evidence_set(
        cls,
        evidence_set: EvidenceSet,
        workspace_id: Optional[UUID] = None,
        organization_id: Optional[UUID] = None
    ) -> EvidenceSet:
        if not evidence_set.items:
            return evidence_set

        graph = KnowledgeGraphService.get_instance()
        registry = EntityRegistry.get_instance()

        for item in evidence_set.items:
            # 1. Resolve title/content to entity
            resolved_entity, ambiguity = EntityResolutionEngine.resolve_mention(
                mention=item.title,
                workspace_id=workspace_id
            )

            if resolved_entity:
                item.metadata["canonical_entity"] = resolved_entity.to_dict()
                
                # Fetch graph neighbors
                neighbors = graph.get_neighbors(
                    entity_id=resolved_entity.entity_id,
                    max_depth=1,
                    organization_id=organization_id,
                    workspace_id=workspace_id
                )
                item.metadata["graph_neighbors"] = [n.to_dict() for n in neighbors]

                # Fetch graph relationships
                rels = graph.get_relationships(
                    entity_id=resolved_entity.entity_id,
                    organization_id=organization_id,
                    workspace_id=workspace_id
                )
                item.metadata["graph_relationships"] = [r.to_dict() for r in rels]

                # Graph connection boost
                if rels:
                    item.score = round(min(1.0, item.score + 0.05), 4)

        return evidence_set
