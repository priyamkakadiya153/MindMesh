import logging
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.database import get_db_session
from ..authorization.organization_resolver import resolve_organization_id
from ..documents.dependencies import get_document_service
from .service import VectorService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/vector", tags=["Vector Platform"])

class RebuildIndexRequest(BaseModel):
    index_name: str

class CreateIndexRequest(BaseModel):
    name: str
    embedding_model: str = "text-embedding-3-small"
    dimensions: int = 1536
    similarity_metric: str = "COSINE"
    index_type: str = "HNSW"

@router.post("/index/rebuild", status_code=status.HTTP_200_OK)
async def rebuild_index(
    request: RebuildIndexRequest,
    org_id: UUID = Depends(resolve_organization_id),
    db: AsyncSession = Depends(get_db_session)
):
    """Rebuilds a specific dynamic vector index for organization."""
    from .index_manager import IndexManager
    manager = IndexManager(db)
    success = await manager.rebuild_index(org_id, request.index_name)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to rebuild index {request.index_name}."
        )
    return {
        "status": "success",
        "message": f"Index {request.index_name} rebuilt successfully."
    }

@router.get("/index", status_code=status.HTTP_200_OK)
async def list_indexes(
    org_id: UUID = Depends(resolve_organization_id),
    db: AsyncSession = Depends(get_db_session)
):
    """Lists all registered vector indexes for active organization."""
    from .index_manager import IndexManager
    manager = IndexManager(db)
    return await manager.get_indexes(org_id)

@router.post("/index", status_code=status.HTTP_201_CREATED)
async def create_index(
    request: CreateIndexRequest,
    org_id: UUID = Depends(resolve_organization_id),
    db: AsyncSession = Depends(get_db_session)
):
    """Registers and creates a new vector ANN index in database."""
    from .index_manager import IndexManager
    manager = IndexManager(db)
    try:
        return await manager.create_index(
            org_id=org_id,
            name=request.name,
            embedding_model=request.embedding_model,
            dimensions=request.dimensions,
            similarity_metric=request.similarity_metric,
            index_type=request.index_type

        )
    except Exception as e:
        logger.exception(f"Failed to create index {request.name}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to register index: {str(e)}"
        )

@router.get("/statistics", status_code=status.HTTP_200_OK)
async def get_statistics(
    org_id: UUID = Depends(resolve_organization_id),
    db: AsyncSession = Depends(get_db_session)
):
    """Returns operational and performance statistics for vector index structures."""
    service = VectorService(db)
    return await service.get_monitoring_stats()

@router.post("/synchronize", status_code=status.HTTP_200_OK)
async def synchronize_vectors(
    org_id: UUID = Depends(resolve_organization_id),
    db: AsyncSession = Depends(get_db_session)
):
    """Detects and fixes missing embeddings on organization's documents."""
    service = VectorService(db)
    return await service.synchronize(org_id)

@router.post("/rebuild", status_code=status.HTTP_200_OK)
async def rebuild_all_organization_vectors(
    org_id: UUID = Depends(resolve_organization_id),
    db: AsyncSession = Depends(get_db_session)
):
    """Deletes and rebuilds all vectors/embeddings for current organization."""
    service = VectorService(db)
    return await service.rebuild(org_id)

@router.delete("/document/{id}", status_code=status.HTTP_200_OK)
async def delete_document_vectors(
    id: UUID,
    org_id: UUID = Depends(resolve_organization_id),
    db: AsyncSession = Depends(get_db_session),
    doc_service = Depends(get_document_service)
):
    """Purges vector embeddings associated with specified document ID."""
    doc = await doc_service.get_document(id)
    if doc.organization_id != org_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found or access denied."
        )
        
    service = VectorService(db)
    count = await service.delete_document_vectors(id)
    return {
        "status": "success",
        "message": f"Deleted {count} vector records associated with document {id}."
    }

@router.post("/optimize", status_code=status.HTTP_200_OK)
async def optimize_indexes(
    org_id: UUID = Depends(resolve_organization_id),
    db: AsyncSession = Depends(get_db_session)
):
    """Optimizes database storage layout and dynamic index nodes."""
    service = VectorService(db)
    return await service.optimize(org_id)

@router.post("/cleanup", status_code=status.HTTP_200_OK)
async def cleanup_orphans(
    org_id: UUID = Depends(resolve_organization_id),
    db: AsyncSession = Depends(get_db_session)
):
    """Performs cleanup of orphaned vectors and indices records."""
    service = VectorService(db)
    return await service.cleanup(org_id)
