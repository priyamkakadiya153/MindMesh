import time
import logging
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from .models import VectorIndex
from .providers.pgvector.indexes import rebuild_pgvector_index
from .metrics import metrics_manager

logger = logging.getLogger(__name__)

class IndexManager:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_indexes(self, org_id: UUID) -> list[VectorIndex]:
        """Retrieves registered vector indexes for the organization."""
        stmt = select(VectorIndex).where(
            VectorIndex.organization_id == org_id,
            VectorIndex.is_active == True
        )
        res = await self.db.execute(stmt)
        return list(res.scalars().all())

    async def create_index(
        self,
        org_id: UUID,
        name: str,
        embedding_model: str = "text-embedding-3-small",
        dimensions: int = 1536,
        similarity_metric: str = "COSINE",
        index_type: str = "HNSW"
    ) -> VectorIndex:
        """Registers a new index and builds it in pgvector."""
        stmt = select(VectorIndex).where(
            VectorIndex.organization_id == org_id,
            VectorIndex.name == name,
            VectorIndex.is_active == True
        )
        res = await self.db.execute(stmt)
        existing = res.scalar_one_or_none()
        if existing:
            return existing

        index_rec = VectorIndex(
            organization_id=org_id,
            name=name,
            embedding_model=embedding_model,
            dimensions=dimensions,
            similarity_metric=similarity_metric,
            index_type=index_type,
            status="REBUILDING"
        )
        self.db.add(index_rec)
        await self.db.flush()

        success = await rebuild_pgvector_index(
            self.db,
            name,
            index_type,
            similarity_metric,
            dimensions
        )

        index_rec.status = "ACTIVE" if success else "FAILED"
        await self.db.commit()
        return index_rec

    async def rebuild_index(self, org_id: UUID, index_name: str) -> bool:
        """Rebuilds an existing index and updates metrics."""
        stmt = select(VectorIndex).where(
            VectorIndex.organization_id == org_id,
            VectorIndex.name == index_name,
            VectorIndex.is_active == True
        )
        res = await self.db.execute(stmt)
        index_rec = res.scalar_one_or_none()
        if not index_rec:
            logger.warning(f"Index {index_name} not found for organization {org_id}")
            return False

        index_rec.status = "REBUILDING"
        await self.db.commit()

        start = time.time()
        success = await rebuild_pgvector_index(
            self.db,
            index_name,
            index_rec.index_type,
            index_rec.similarity_metric,
            index_rec.dimensions
        )
        duration = time.time() - start
        metrics_manager.record_rebuild(duration)

        index_rec.status = "ACTIVE" if success else "FAILED"
        await self.db.commit()
        return success
