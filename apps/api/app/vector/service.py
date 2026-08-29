import time
import logging
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from .repository import VectorRepository
from .lifecycle import LifecycleManager
from .index_manager import IndexManager
from .maintenance import MaintenanceManager
from .monitoring import VectorMonitor
from .metrics import metrics_manager

logger = logging.getLogger(__name__)

class VectorService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = VectorRepository(db)
        self.lifecycle = LifecycleManager(db)
        self.index_manager = IndexManager(db)
        self.maintenance = MaintenanceManager(db)
        self.monitor = VectorMonitor(db)

    async def search_similarity(
        self,
        org_id: UUID,
        query_vector: list[float],
        limit: int = 5,
        metric: str = "COSINE",
        filters: dict = None
    ) -> list[dict]:
        """Performs multi-tenant isolated similarity search and records latency."""
        # Enforce strict organization boundary isolation
        final_filters = dict(filters) if filters else {}
        final_filters["organization_id"] = str(org_id)
        
        start = time.time()
        results = await self.repo.search(query_vector, limit, metric, final_filters)
        latency = (time.time() - start) * 1000.0 # latency in milliseconds
        
        metrics_manager.record_search(latency)
        return results

    async def delete_document_vectors(self, document_id: UUID) -> int:
        """Invokes removal of vectors associated with document."""
        return await self.lifecycle.delete_vectors(document_id)

    async def synchronize(self, org_id: UUID) -> dict:
        """Runs syncer routine to catch up missing embeddings."""
        return await self.lifecycle.synchronize(org_id)

    async def rebuild(self, org_id: UUID) -> dict:
        """Triggers complete reconstruction of all vectors for organization."""
        return await self.lifecycle.rebuild_all_vectors(org_id)

    async def optimize(self, org_id: UUID) -> dict:
        """Performs database-level indexing maintenance optimizations."""
        return await self.maintenance.optimize_indexes(org_id)

    async def cleanup(self, org_id: UUID) -> dict:
        """Purges orphaned embedding elements from vector space."""
        return await self.maintenance.cleanup_orphaned_vectors(org_id)

    async def get_monitoring_stats(self) -> dict:
        """Gathers aggregated vector database monitoring metrics."""
        return await self.monitor.get_system_stats()
