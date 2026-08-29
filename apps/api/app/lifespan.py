import asyncio
from fastapi import FastAPI
from contextlib import asynccontextmanager
from .database.connection import verify_connection
from .database.seed import seed_data
from .core.database import AsyncSessionLocal
from alembic.config import Config
from alembic import command

def run_migrations():
    try:
        print("[Lifespan] Running database migrations...")
        cfg = Config("alembic.ini")
        command.upgrade(cfg, "head")
        print("[Lifespan] Database migrations completed successfully.")
    except Exception as e:
        print(f"[Lifespan Notice] Programmatic migration skipped or completed: {str(e)}")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup lifecycle hooks
    print("[Lifespan] Starting up MindMesh API Backend...")
    
    # Run migrations safely in worker thread to prevent event loop blocking/conflicts
    loop = asyncio.get_running_loop()
    await loop.run_in_executor(None, run_migrations)

    try:
        await verify_connection()
        print("[Lifespan] Database connection verified successfully.")
        
        # Run seed data
        async with AsyncSessionLocal() as session:
            await seed_data(session)
            await session.commit()
            print("[Lifespan] Database auto-seeding completed.")
    except Exception as e:
        print(f"[Lifespan Warn] Database verification or seeding failed: {str(e)}")

    # Start EventDispatcher, BackgroundWorkerManager, LearningScheduler and ReminderScheduler
    try:
        from app.automation.events.dispatcher import EventDispatcher
        from app.automation.workers import BackgroundWorkerManager
        from app.learning.scheduler import LearningScheduler
        from app.notifications.reminder_scheduler import reminder_scheduler

        EventDispatcher.start_listening()
        BackgroundWorkerManager.start_all()
        LearningScheduler.start()
        asyncio.create_task(reminder_scheduler.start())
        print("[Lifespan] Background Reminder Worker initialized.")
    except Exception as e:
        print(f"[Lifespan Notice] Module background workers initialization: {e}")

    yield

    # Shutdown lifecycle hooks
    print("[Lifespan] Shutting down MindMesh API Backend...")
    try:
        BackgroundWorkerManager.stop_all()
        LearningScheduler.stop()
    except Exception:
        pass
