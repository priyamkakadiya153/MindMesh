import logging
from sqlalchemy.ext.asyncio import AsyncSession
from .maintenance import MaintenanceManager

logger = logging.getLogger(__name__)

async def run_nightly_maintenance(db: AsyncSession, org_id: any) -> bool:
    """Nightly scheduler job to optimize vector database indexes and purge orphans."""
    logger.info("Initializing scheduled vector maintenance routine.")
    manager = MaintenanceManager(db)
    
    # 1. Clean orphans
    cleanup_res = await manager.cleanup_orphaned_vectors(org_id)
    logger.info(f"Purged orphaned vector records: {cleanup_res}")
    
    # 2. Defragment indexes
    opt_res = await manager.optimize_indexes(org_id)
    logger.info(f"Optimization task outcome: {opt_res}")
    
    return True
