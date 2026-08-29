import pytest
import asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from app.automation.workers import BackgroundWorkerManager
from app.automation.workers.monitoring import WorkerQueueMonitor

@pytest.mark.asyncio
async def test_background_workers_lifecycle():
    # 1. Start all workers daemon loops
    BackgroundWorkerManager.start_all()
    assert BackgroundWorkerManager._is_active is True
    
    # Check monitor stats
    stats = WorkerQueueMonitor.get_active_worker_stats()
    assert stats["workflow_worker_active"] is True
    assert stats["scheduler_worker_active"] is True
    
    # Let task loop cycles execute once
    await asyncio.sleep(0.5)

    # 2. Teardown all workers
    BackgroundWorkerManager.stop_all()
    assert BackgroundWorkerManager._is_active is False
