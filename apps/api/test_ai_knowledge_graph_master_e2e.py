import time
import uuid
import pytest
from app.ai.knowledge.entity_models import (
    CanonicalEntity,
    EntityType,
    EntityStatus,
    ConfidenceLevel
)
from app.ai.knowledge.entity_resolution import EntityRegistry, EntityResolutionEngine
from app.ai.knowledge.graph_models import (
    GraphNode,
    GraphEdge,
    RelationshipType,
    EdgeStatus
)
from app.ai.knowledge.graph_service import KnowledgeGraphService
from app.ai.knowledge.graph_retrieval import EntityAwareRetrievalBridge
from app.ai.retrieval.models import EvidenceSet, EvidenceItem, SourceType

def test_canonical_entity_registration_and_alias():
    registry = EntityRegistry.get_instance()
    eid = uuid.uuid4()
    ws_id = uuid.uuid4()

    entity = CanonicalEntity(
        entity_id=eid,
        entity_type=EntityType.PROJECT,
        canonical_name="Project Alpha",
        display_name="Project Alpha",
        aliases=["Alpha", "Alpha project"],
        identifiers={"jira": "PROJ-101"},
        workspace_id=ws_id
    )
    registry.register(entity)

    # Resolve exact name
    res_name, _ = EntityResolutionEngine.resolve_mention("Project Alpha", workspace_id=ws_id)
    assert res_name is not None
    assert res_name.entity_id == eid

    # Resolve alias
    res_alias, _ = EntityResolutionEngine.resolve_mention("Alpha", workspace_id=ws_id)
    assert res_alias is not None
    assert res_alias.entity_id == eid

    # Resolve identifier
    res_id, _ = EntityResolutionEngine.resolve_mention("JIRA:PROJ-101", workspace_id=ws_id)
    assert res_id is not None
    assert res_id.entity_id == eid

def test_entity_ambiguity_detection():
    registry = EntityRegistry.get_instance()
    ws_id = uuid.uuid4()

    proj = CanonicalEntity(
        entity_id=uuid.uuid4(),
        entity_type=EntityType.PROJECT,
        canonical_name="Beta",
        display_name="Project Beta",
        aliases=["Beta"],
        workspace_id=ws_id
    )
    team = CanonicalEntity(
        entity_id=uuid.uuid4(),
        entity_type=EntityType.TEAM,
        canonical_name="Beta",
        display_name="Team Beta",
        aliases=["Beta"],
        workspace_id=ws_id
    )
    registry.register(proj)
    registry.register(team)

    res, ambiguity = EntityResolutionEngine.resolve_mention("Beta", workspace_id=ws_id)
    assert res is None
    assert ambiguity is not None
    assert len(ambiguity.candidates) == 2
    assert ambiguity.clarification_prompt is not None

def test_graph_node_and_directional_edge():
    graph = KnowledgeGraphService.get_instance()
    ws_id = uuid.uuid4()

    e1 = CanonicalEntity(entity_id=uuid.uuid4(), entity_type=EntityType.PROJECT, canonical_name="P1", display_name="P1", workspace_id=ws_id)
    e2 = CanonicalEntity(entity_id=uuid.uuid4(), entity_type=EntityType.TASK, canonical_name="T1", display_name="T1", workspace_id=ws_id)

    graph.add_node(e1)
    graph.add_node(e2)

    edge = graph.add_edge(
        source_id=e1.entity_id,
        target_id=e2.entity_id,
        rel_type=RelationshipType.OWNS,
        workspace_id=ws_id
    )

    rels = graph.get_relationships(e1.entity_id, workspace_id=ws_id)
    assert len(rels) == 1
    assert rels[0].relationship_type == RelationshipType.OWNS

    nbrs = graph.get_neighbors(e1.entity_id, workspace_id=ws_id)
    assert len(nbrs) == 1
    assert nbrs[0].entity_id == e2.entity_id

def test_graph_path_discovery_and_cycle_protection():
    graph = KnowledgeGraphService.get_instance()
    ws_id = uuid.uuid4()

    eA = CanonicalEntity(entity_id=uuid.uuid4(), entity_type=EntityType.SERVICE, canonical_name="A", display_name="A", workspace_id=ws_id)
    eB = CanonicalEntity(entity_id=uuid.uuid4(), entity_type=EntityType.SERVICE, canonical_name="B", display_name="B", workspace_id=ws_id)
    eC = CanonicalEntity(entity_id=uuid.uuid4(), entity_type=EntityType.SERVICE, canonical_name="C", display_name="C", workspace_id=ws_id)

    graph.add_node(eA)
    graph.add_node(eB)
    graph.add_node(eC)

    # Cycle: A -> B -> C -> A
    graph.add_edge(eA.entity_id, eB.entity_id, RelationshipType.DEPENDS_ON, workspace_id=ws_id)
    graph.add_edge(eB.entity_id, eC.entity_id, RelationshipType.DEPENDS_ON, workspace_id=ws_id)
    graph.add_edge(eC.entity_id, eA.entity_id, RelationshipType.DEPENDS_ON, workspace_id=ws_id)

    path = graph.find_path(eA.entity_id, eC.entity_id, max_hops=3, workspace_id=ws_id)
    assert len(path) == 2
    assert path[0].source_entity_id == eA.entity_id
    assert path[1].target_entity_id == eC.entity_id

def test_graph_temporal_edge_validity():
    edge_past = GraphEdge(
        edge_id=uuid.uuid4(),
        source_entity_id=uuid.uuid4(),
        target_entity_id=uuid.uuid4(),
        relationship_type=RelationshipType.OWNS,
        valid_from=time.time() - 3600,
        valid_until=time.time() - 100
    )
    assert edge_past.is_currently_valid() is False

def test_cross_tenant_graph_isolation():
    graph = KnowledgeGraphService.get_instance()
    ws1 = uuid.uuid4()
    ws2 = uuid.uuid4()

    e1 = CanonicalEntity(entity_id=uuid.uuid4(), entity_type=EntityType.PROJECT, canonical_name="P_WS1", display_name="P_WS1", workspace_id=ws1)
    e2 = CanonicalEntity(entity_id=uuid.uuid4(), entity_type=EntityType.TASK, canonical_name="T_WS1", display_name="T_WS1", workspace_id=ws1)

    graph.add_node(e1)
    graph.add_node(e2)
    graph.add_edge(e1.entity_id, e2.entity_id, RelationshipType.OWNS, workspace_id=ws1)

    # Querying from ws2 must return 0 neighbors/edges
    nbrs = graph.get_neighbors(e1.entity_id, workspace_id=ws2)
    assert len(nbrs) == 0

def test_entity_aware_retrieval_enrichment():
    registry = EntityRegistry.get_instance()
    graph = KnowledgeGraphService.get_instance()
    ws_id = uuid.uuid4()

    proj = CanonicalEntity(
        entity_id=uuid.uuid4(),
        entity_type=EntityType.PROJECT,
        canonical_name="Gamma",
        display_name="Project Gamma",
        aliases=["Gamma"],
        workspace_id=ws_id
    )
    registry.register(proj)
    graph.add_node(proj)

    item = EvidenceItem(
        source_id="101",
        source_type=SourceType.DOCUMENT,
        title="Project Gamma",
        content="Details about Gamma",
        score=0.80
    )
    ev_set = EvidenceSet(query="Tell me about Gamma", items=[item])

    enriched = EntityAwareRetrievalBridge.enrich_evidence_set(ev_set, workspace_id=ws_id)
    assert len(enriched.items) == 1
    assert "canonical_entity" in enriched.items[0].metadata
    assert enriched.items[0].metadata["canonical_entity"]["canonical_name"] == "Gamma"
