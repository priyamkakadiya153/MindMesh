from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Any
from datetime import datetime
from uuid import UUID

# Legacy schemas retained for backward compatibility
class SearchRequest(BaseModel):
    query: str
    limit: Optional[int] = 10
    filters: Optional[Dict[str, Any]] = None

class MetadataSearchRequest(BaseModel):
    filters: Dict[str, Any]
    limit: Optional[int] = 10

class MatchedChunkSchema(BaseModel):
    chunk_id: str
    content: str
    page: int

class SearchResultItem(BaseModel):
    document_id: str
    title: str
    score: float
    snippet: str
    page: int
    workspace: str
    project: str
    tags: List[str]
    matched_chunks: List[MatchedChunkSchema]

class SearchResponse(BaseModel):
    results: List[SearchResultItem]
    query_time_ms: float
    total_hits: int

# Phase 2 Universal Search Schemas

class UniversalSearchResultItem(BaseModel):
    id: str
    entity_type: Optional[str] = "document"
    entity_id: Optional[str] = None
    source_type: Optional[str] = "document"
    source_id: Optional[str] = None
    title: str
    snippet: str
    workspace_id: Optional[str] = None
    workspace_name: Optional[str] = None
    organization_id: Optional[str] = None
    organization_name: Optional[str] = None
    owner_id: Optional[str] = None
    tags: List[str] = []
    metadata: Dict[str, Any] = {}
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    score: float
    deep_link: Optional[str] = None

class UniversalSearchResponse(BaseModel):
    results: List[UniversalSearchResultItem]
    total_hits: int
    page: int
    limit: int
    total_pages: int
    query_time_ms: float
    facets: Dict[str, int] = {}

class AutocompleteSuggestion(BaseModel):
    id: str
    title: str
    type: str
    workspace_id: Optional[str] = None

class SearchHistoryResponseItem(BaseModel):
    id: str
    query: str
    created_at: str

class ClearHistoryResponse(BaseModel):
    success: bool
    message: str
