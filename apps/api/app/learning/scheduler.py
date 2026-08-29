import logging
import asyncio
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import AsyncSessionLocal
from app.learning.feedback import FeedbackProcessor
from app.memory.service import MemoryService
from app.memory.repository import MemoryRepository

logger = logging.getLogger(__name__)

class LearningScheduler:
    _loop_task = None
    _running = False

    @classmethod
    def start(cls):
        """Starts the learning trainer background scheduler."""
        if cls._running:
            return
        cls._running = True
        cls._loop_task = asyncio.create_task(cls._poll_loop())
        logger.info("LearningScheduler: Started learning training loop daemon.")

    @classmethod
    def stop(cls):
        """Stops the learning scheduler."""
        cls._running = False
        if cls._loop_task:
            cls._loop_task.cancel()
            cls._loop_task = None

    @classmethod
    async def _poll_loop(cls):
        while cls._running:
            try:
                async with AsyncSessionLocal() as db:
                    await cls.process_pending_feedback_sweep(db)
                    await db.commit()
            except Exception as e:
                logger.error(f"LearningScheduler: Error processing learning sweep: {str(e)}", exc_info=True)
            await asyncio.sleep(5.0)

    @classmethod
    async def process_pending_feedback_sweep(cls, db: AsyncSession):
        """Processes unprocessed feedback records, converting ratings into user preference memories."""
        # Find unprocessed feedbacks
        from app.memory.models import AgentFeedback
        stmt_fb = select(AgentFeedback).where(AgentFeedback.processed == False)
        res_fb = await db.execute(stmt_fb)
        feedbacks = res_fb.scalars().all()

        for fb in feedbacks:
            # If positive rating, save or update user memory preference
            if fb.rating >= 4:
                # Resolve existing user preference memory
                existing = await MemoryRepository.list_memories(
                    db=db,
                    organization_id=fb.organization_id,
                    memory_type="User",
                    scope_key=str(fb.user_id),
                    key="preferred_style"
                )

                style_val = {"interaction_style": fb.comment or "verbose", "adapted_at": str(fb.created_at)}
                if existing:
                    # Update
                    m = existing[0]
                    m.value = style_val
                    m.confidence_score = 1.0
                else:
                    # Create
                    await MemoryService.add_memory(
                        db=db,
                        organization_id=fb.organization_id,
                        memory_type="User",
                        scope_key=str(fb.user_id),
                        key="preferred_style",
                        value=style_val,
                        importance_score=0.9,
                        confidence_score=1.0
                    )

            fb.processed = True
            db.add(fb)
            
        if feedbacks:
            await db.flush()
            logger.info(f"LearningScheduler: Successfully processed {len(feedbacks)} pending feedback logs.")
