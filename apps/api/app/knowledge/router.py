from fastapi import APIRouter, Depends, HTTPException, status
from uuid import UUID
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from ..core.database import get_db_session
from ..api.dependencies import get_current_user
from ..authorization.organization_resolver import resolve_organization_id
from ..models.user import User
from ..documents.dependencies import get_document_service
from ..documents.service import DocumentService
from .schemas import KnowledgeResponse, SummaryResponse, QualityResponse, ProcessingEventResponse
from .service import KnowledgeService
from ..processing.orchestrator import ProcessingOrchestrator
from ..processing.schemas import StatisticsResponse, ProcessResponse
from .models import ProcessingEvent, DocumentStatistic

router = APIRouter(prefix="", tags=["knowledge"])

@router.get("/knowledge/{documentId}", response_model=KnowledgeResponse)
async def get_document_knowledge(
    documentId: UUID,
    org_id: UUID = Depends(resolve_organization_id),
    db: AsyncSession = Depends(get_db_session),
    doc_service: DocumentService = Depends(get_document_service)
):
    doc = await doc_service.get_document(documentId)
    if doc.organization_id != org_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found or access is denied."
        )
        
    k_service = KnowledgeService(db)
    knowledge = await k_service.get_knowledge(documentId)
    if not knowledge:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Document has not been processed into knowledge yet."
        )
        
    return knowledge

@router.get("/knowledge/{documentId}/summary", response_model=SummaryResponse)
async def get_document_summary(
    documentId: UUID,
    org_id: UUID = Depends(resolve_organization_id),
    db: AsyncSession = Depends(get_db_session),
    doc_service: DocumentService = Depends(get_document_service)
):
    doc = await doc_service.get_document(documentId)
    if doc.organization_id != org_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found or access is denied."
        )
        
    k_service = KnowledgeService(db)
    knowledge = await k_service.get_knowledge(documentId)
    if not knowledge or not knowledge.summary:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Summary is not available for this document."
        )
        
    return SummaryResponse(document_id=documentId, summary=knowledge.summary)

@router.get("/knowledge/{documentId}/statistics", response_model=StatisticsResponse)
async def get_document_statistics_metric(
    documentId: UUID,
    org_id: UUID = Depends(resolve_organization_id),
    db: AsyncSession = Depends(get_db_session),
    doc_service: DocumentService = Depends(get_document_service)
):
    doc = await doc_service.get_document(documentId)
    if doc.organization_id != org_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found or access is denied."
        )
        
    k_service = KnowledgeService(db)
    stats = await k_service.get_statistics(documentId)
    if not stats:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Statistics are not generated for this document."
        )
        
    return StatisticsResponse(
        document_id=documentId,
        word_count=stats.words,
        character_count=stats.characters,
        page_count=stats.pages,
        table_count=stats.tables,
        image_count=stats.images
    )

@router.post("/documents/{id}/reprocess", response_model=ProcessResponse)
async def reprocess_document_manually(
    id: UUID,
    org_id: UUID = Depends(resolve_organization_id),
    db: AsyncSession = Depends(get_db_session),
    doc_service: DocumentService = Depends(get_document_service)
):
    doc = await doc_service.get_document(id)
    if doc.organization_id != org_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found or access is denied."
        )
        
    orchestrator = ProcessingOrchestrator(db)
    await orchestrator.orchestrate(id)
    
    return ProcessResponse(
        document_id=id,
        status="success",
        message="Orchestrator successfully reprocessed scanned inputs."
    )

@router.get("/documents/{id}/processing", response_model=List[ProcessingEventResponse])
async def get_document_processing_events(
    id: UUID,
    org_id: UUID = Depends(resolve_organization_id),
    db: AsyncSession = Depends(get_db_session),
    doc_service: DocumentService = Depends(get_document_service)
):
    doc = await doc_service.get_document(id)
    if doc.organization_id != org_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found or access is denied."
        )
        
    stmt = select(ProcessingEvent).where(ProcessingEvent.document_id == id).order_by(ProcessingEvent.timestamp)
    result = await db.execute(stmt)
    return list(result.scalars().all())

@router.get("/documents/{id}/quality", response_model=QualityResponse)
async def get_document_quality(
    id: UUID,
    org_id: UUID = Depends(resolve_organization_id),
    db: AsyncSession = Depends(get_db_session),
    doc_service: DocumentService = Depends(get_document_service)
):
    doc = await doc_service.get_document(id)
    if doc.organization_id != org_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found or access is denied."
        )
        
    k_service = KnowledgeService(db)
    knowledge = await k_service.get_knowledge(id)
    if not knowledge:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Quality score is not available."
        )
        
    return QualityResponse(
        document_id=id,
        quality_score=knowledge.quality_score,
        is_completeness_valid=knowledge.quality_score >= 0.70
    )
