import uuid
import pytest
from app.ai.intent.engine import IntentEngine
from app.ai.retrieval.models import (
    RetrievalRequest,
    RetrievalPlan,
    EvidenceItem,
    EvidenceSet,
    EvidenceCoverage,
    SourceType
)
from app.ai.retrieval.planner import RetrievalPlanner
from app.ai.retrieval.reranker import RetrievalReranker
from app.ai.retrieval.adapters.structured import StructuredDataSearchAdapter
from app.ai.retrieval.adapters.conversation import ConversationSearchAdapter
from app.ai.retrieval.engine import HybridRetrievalEngine

def test_planner_no_retrieval_for_greeting():
    intent_res = IntentEngine.understand_query("hi")
    req = RetrievalRequest(
        request_id="r1",
        original_query="hi",
        user_id=uuid.uuid4(),
        organization_id=uuid.uuid4(),
        intent_result=intent_res
    )
    plan = RetrievalPlanner.plan(req)
    assert len(plan.sources) == 0
    assert plan.rerank_required is False

def test_planner_structured_retrieval_for_project_query():
    intent_res = IntentEngine.understand_query("What projects are active?")
    req = RetrievalRequest(
        request_id="r2",
        original_query="What projects are active?",
        user_id=uuid.uuid4(),
        organization_id=uuid.uuid4(),
        intent_result=intent_res
    )
    plan = RetrievalPlanner.plan(req)
    assert SourceType.PROJECT in plan.sources
    assert plan.rerank_required is True

def test_planner_document_retrieval():
    intent_res = IntentEngine.understand_query("What does architecture.pdf say about authentication?")
    req = RetrievalRequest(
        request_id="r3",
        original_query="What does architecture.pdf say about authentication?",
        user_id=uuid.uuid4(),
        organization_id=uuid.uuid4(),
        intent_result=intent_res
    )
    plan = RetrievalPlanner.plan(req)
    assert SourceType.DOCUMENT in plan.sources

def test_planner_conversation_retrieval():
    intent_res = IntentEngine.understand_query("What did we discuss yesterday about OAuth?")
    req = RetrievalRequest(
        request_id="r4",
        original_query="What did we discuss yesterday about OAuth?",
        user_id=uuid.uuid4(),
        organization_id=uuid.uuid4(),
        intent_result=intent_res
    )
    plan = RetrievalPlanner.plan(req)
    assert SourceType.CONVERSATION in plan.sources or SourceType.MESSAGE in plan.sources

def test_reranker_deduplication_and_scoring():
    item1 = EvidenceItem(
        source_id="1",
        source_type=SourceType.DOCUMENT,
        title="Doc 1",
        content="Authentication using OAuth2",
        score=0.80,
        authority_score=0.85,
        recency_score=0.90,
        retrieval_methods=["semantic"]
    )
    item2 = EvidenceItem(
        source_id="1",
        source_type=SourceType.DOCUMENT,
        title="Doc 1",
        content="Authentication using OAuth2",
        score=0.75,
        authority_score=0.85,
        recency_score=0.90,
        retrieval_methods=["keyword"]
    )
    item3 = EvidenceItem(
        source_id="2",
        source_type=SourceType.PROJECT,
        title="Project Alpha",
        content="Backend auth project",
        score=0.90,
        authority_score=0.95,
        recency_score=0.95,
        retrieval_methods=["structured_db"]
    )

    plan = RetrievalPlan(sources=[SourceType.DOCUMENT, SourceType.PROJECT], queries=["OAuth2"], max_results=5)
    reranked = RetrievalReranker.rerank([item1, item2, item3], plan, intent_entities=["OAuth2"])

    assert len(reranked) == 2
    # Duplicate item1 and item2 merged methods
    doc_item = [i for i in reranked if i.source_id == "1"][0]
    assert "semantic" in doc_item.retrieval_methods
    assert "keyword" in doc_item.retrieval_methods

@pytest.mark.asyncio
async def test_engine_permission_isolation():
    from unittest.mock import AsyncMock, MagicMock

    user_id = uuid.uuid4()
    unauth_org_id = uuid.uuid4()

    mock_db = AsyncMock()
    mock_res = MagicMock()
    mock_res.scalar_one_or_none.return_value = None
    mock_db.execute.return_value = mock_res

    intent_res = IntentEngine.understand_query("What projects exist?")
    req = RetrievalRequest(
        request_id="r5",
        original_query="What projects exist?",
        user_id=user_id,
        organization_id=unauth_org_id,
        intent_result=intent_res
    )
    engine = HybridRetrievalEngine(mock_db)
    res = await engine.retrieve_knowledge(req)

    assert res.coverage == EvidenceCoverage.NONE
    assert res.confidence == "INSUFFICIENT"
    assert res.trace.get("error") == "PERMISSION_FILTERED"
