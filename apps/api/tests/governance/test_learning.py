import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from app.learning.engine import LearningEngine
from app.learning.feedback import FeedbackProcessor
from app.learning.adaptation import AdaptationLayer
from app.learning.trainer import AgentTrainer
from app.learning.evaluator import MemoryEvaluator
from app.learning.scheduler import LearningScheduler
from app.memory.service import MemoryService
from tests.agents.test_sdk import seed_agent_test_data

@pytest.mark.asyncio
async def test_learning_feedback_and_adaptation(db_session: AsyncSession):
    user, org = await seed_agent_test_data(db_session)

    # 1. Log positive feedback
    await LearningEngine.learn(
        db=db_session,
        user_id=user.id,
        organization_id=org.id,
        rating=5,
        comment="Prefer bulleted summaries",
        context_data={"style": "concise", "format": "bullets"}
    )

    await LearningEngine.learn(
        db=db_session,
        user_id=user.id,
        organization_id=org.id,
        rating=4,
        comment="Excellent speed",
        context_data={"style": "concise", "format": "bullets"}
    )

    # Log negative feedback (should be excluded from adaptation)
    await LearningEngine.learn(
        db=db_session,
        user_id=user.id,
        organization_id=org.id,
        rating=2,
        comment="Too verbose",
        context_data={"style": "verbose"}
    )
    
    await db_session.commit()

    # 2. Test adaptation layer overrides calculation
    overrides = await LearningEngine.retrieve_adapted_context(
        db=db_session,
        organization_id=org.id,
        user_id=user.id
    )

    assert overrides["style"] == "concise"
    assert overrides["preferred_format"] == "bullets"

def test_trainer_and_evaluator():
    # Trainer plan recommendation
    history = [
        {"tools": ["search_documents", "read_file"]},
        {"tools": ["search_documents", "read_file", "summarize_text"]}
    ]
    pattern = AgentTrainer.extract_pattern(history)
    assert "search_documents" in pattern["recommended_tools"]
    assert "read_file" in pattern["recommended_tools"]

    # Evaluator quality scoring
    quality = MemoryEvaluator.evaluate_quality("theme_pref", {"theme": "dark", "history": ["old_theme"]})
    assert quality > 0.6

@pytest.mark.asyncio
async def test_learning_scheduler_sweep(db_session: AsyncSession):
    user, org = await seed_agent_test_data(db_session)

    # Create unprocessed positive feedback
    await FeedbackProcessor.record_feedback(
        db=db_session,
        user_id=user.id,
        organization_id=org.id,
        feedback_type="explicit_rating",
        rating=5,
        comment="formal style"
    )
    await db_session.commit()

    # Run pending learning sweeps
    await LearningScheduler.process_pending_feedback_sweep(db_session)
    await db_session.commit()

    # Verify that memory record has been spawned
    context = await MemoryService.search_memories(
        db=db_session,
        organization_id=org.id,
        user_id=user.id,
        query_key="preferred_style"
    )
    assert len(context) == 1
    assert context[0]["value"]["interaction_style"] == "formal style"
