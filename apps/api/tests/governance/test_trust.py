import pytest
import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from app.governance.trust import TrustScorer
from app.governance.explainability import ExplainabilityTrace
from app.governance.auditing import ActionAuditor
from tests.agents.test_sdk import seed_agent_test_data

def test_composite_trust_scorer():
    # Calculated weighted score test
    score = TrustScorer.calculate_trust_score(
        knowledge_quality=1.0,        # 0.25
        retrieval_confidence=0.8,     # 0.20
        policy_compliance=1.0,        # 0.20
        tool_reliability=0.9,         # 0.135
        workflow_success=0.8          # 0.120
    )                                 # Total: 0.905
    assert score == 0.905

    # Out of bounds clamping
    clamped = TrustScorer.calculate_trust_score(2.0, -1.0, 1.0, 1.0, 1.0)
    assert clamped <= 1.0
    assert clamped >= 0.0

@pytest.mark.asyncio
async def test_explainability_trace_report(db_session: AsyncSession):
    user, org = await seed_agent_test_data(db_session)
    run_id = uuid.uuid4()

    # Log action trace
    await ActionAuditor.log_action_decision(
        db=db_session,
        execution_id=run_id,
        organization_id=org.id,
        agent_name="ResearchAgent",
        selected_tools=["search_web"],
        retrieved_documents=[{"title": "guideline.pdf", "similarity": 0.85}],
        applied_policies=["PII restriction"],
        confidence_score=0.95,
        risk_score=0.05,
        trust_score=0.96,
        execution_summary="Fetched regulatory documentation."
    )
    await db_session.commit()

    # Generate explainability report
    report = await ExplainabilityTrace.generate_explainability_report(db_session, run_id)
    
    assert report is not None
    assert report["agent_name"] == "ResearchAgent"
    assert "search_web" in report["selected_tools"]
    assert report["retrieved_documents"][0]["title"] == "guideline.pdf"
    assert report["trust_score"] == 0.96
    
    # Assert that raw internal chain-of-thought or prompt reasoning properties are NOT leaked
    assert "reasoning_steps" not in report
    assert "internal_chain" not in report
