from sqlalchemy.ext.asyncio import AsyncSession
from .metrics import metrics_manager
from .repository import VectorRepository

class VectorMonitor:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = VectorRepository(db)

    async def get_system_stats(self) -> dict:
        """Retrieves global system-level vector database monitoring statistics."""
        provider_stats = await self.repo.get_statistics()
        mem_metrics = metrics_manager.get_metrics()
        
        # Compute combined counts
        total_vectors = provider_stats.get("vector_count", 0) or mem_metrics.get("total_vectors", 0)
        index_size = provider_stats.get("index_size_bytes", 0)
        active_indexes = provider_stats.get("index_count", 0) or mem_metrics.get("active_indexes", 0)
        
        return {
            "total_vectors": total_vectors,
            "active_indexes": active_indexes,
            "query_latency_ms": mem_metrics["query_latency_ms"],
            "insert_rate": mem_metrics["insert_rate"],
            "delete_rate": mem_metrics["delete_rate"],
            "index_size_bytes": index_size,
            "cache_hit_rate": mem_metrics["cache_hit_rate"],
            "failed_jobs": mem_metrics["failed_jobs"],
            "search_count": mem_metrics["search_count"]
        }
