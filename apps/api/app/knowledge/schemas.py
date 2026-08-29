from pydantic import BaseModel
from uuid import UUID
from datetime import datetime
from typing import List, Dict, Any, Optional

class KnowledgeResponse(BaseModel):
    id: UUID
    document_id: UUID
    extracted_text: str
    normalized_content: Dict[str, Any]
    language: str
    summary: Optional[str] = None
    keywords: Optional[Dict[str, Any]] = None
    topics: Optional[Dict[str, Any]] = None
    quality_score: float
    processing_state: str
    created_at: datetime

    class Config:
        from_attributes = True

class SummaryResponse(BaseModel):
    document_id: UUID
    summary: str

class QualityResponse(BaseModel):
    document_id: UUID
    quality_score: float
    is_completeness_valid: bool

class ProcessingEventResponse(BaseModel):
    id: UUID
    document_id: UUID
    stage: str
    worker: str
    duration_ms: int
    status: str
    error: Optional[str] = None
    timestamp: datetime

    class Config:
        from_attributes = True
