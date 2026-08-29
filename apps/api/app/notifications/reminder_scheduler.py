import logging
import asyncio
from datetime import datetime, timezone
from uuid import uuid4
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import AsyncSessionLocal
from app.notifications.reminder_model import Reminder
from app.notifications.models import Notification

logger = logging.getLogger(__name__)

class ReminderSchedulerWorker:
    """Background worker that periodically checks for due reminders and delivers in-app notifications."""

    _is_running = False

    @classmethod
    async def start(cls, interval_seconds: int = 10):
        if cls._is_running:
            return
        cls._is_running = True
        logger.info("[AUTO-02 REMINDER SCHEDULER] Background worker started.")

        while cls._is_running:
            try:
                await cls.process_due_reminders()
            except Exception as e:
                logger.error(f"[AUTO-02 REMINDER SCHEDULER] Error processing reminders: {str(e)}", exc_info=True)
            await asyncio.sleep(interval_seconds)

    @classmethod
    def stop(cls):
        cls._is_running = False

    @classmethod
    async def process_due_reminders(cls):
        async with AsyncSessionLocal() as db:
            now_utc = datetime.now(timezone.utc)

            # Query due SCHEDULED reminders
            stmt = select(Reminder).where(
                Reminder.status == "SCHEDULED",
                Reminder.scheduled_at <= now_utc
            ).limit(20)

            res = await db.execute(stmt)
            due_reminders = res.scalars().all()

            for rem in due_reminders:
                try:
                    # 1. Mark status = TRIGGERED
                    rem.status = "TRIGGERED"

                    # 2. Insert in-app Notification record
                    notif = Notification(
                        id=uuid4(),
                        user_id=rem.user_id,
                        organization_id=rem.organization_id,
                        title="⏰ MindMesh Reminder",
                        message=rem.title,
                        type="reminder",
                        priority="normal",
                        is_read=False,
                        entity_type="REMINDER",
                        entity_id=rem.id,
                        created_at=datetime.utcnow()
                    )
                    db.add(notif)

                    # 3. Mark status = COMPLETED
                    rem.status = "COMPLETED"

                    await db.commit()
                    logger.info(f"[AUTO-02 REMINDER FIRED SUCCESS] Delivered reminder '{rem.title}' to user {rem.user_id}")

                except Exception as e:
                    logger.error(f"[AUTO-02 REMINDER EXECUTION ERROR] Failed firing reminder {rem.id}: {str(e)}")
                    await db.rollback()

reminder_scheduler = ReminderSchedulerWorker()
