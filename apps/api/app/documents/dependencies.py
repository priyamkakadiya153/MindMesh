from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from ..core.database import get_db_session
from .service import DocumentService
from ..services.metadata_service import MetadataService
from ..services.version_service import VersionService
from ..services.lifecycle_service import LifecycleService
from .governance import GovernanceService
from .history import HistoryService

async def get_document_service(
    db: AsyncSession = Depends(get_db_session)
) -> DocumentService:
    return DocumentService(db)

async def get_metadata_service(
    db: AsyncSession = Depends(get_db_session)
) -> MetadataService:
    return MetadataService(db)

async def get_version_service(
    db: AsyncSession = Depends(get_db_session)
) -> VersionService:
    return VersionService(db)

async def get_lifecycle_service(
    db: AsyncSession = Depends(get_db_session)
) -> LifecycleService:
    return LifecycleService(db)

async def get_governance_service(
    db: AsyncSession = Depends(get_db_session)
) -> GovernanceService:
    return GovernanceService(db)

async def get_history_service(
    db: AsyncSession = Depends(get_db_session)
) -> HistoryService:
    return HistoryService(db)
