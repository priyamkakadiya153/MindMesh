from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from uuid import UUID
from pydantic import BaseModel
from datetime import datetime

class SearchResultItem(BaseModel):
    id: UUID
    type: str # message, file, project, member, conversation
    title: str
    snippet: str
    location: str
    author_name: Optional[str] = None
    created_at: datetime
    metadata: Optional[Dict[str, Any]] = None

class SearchResponse(BaseModel):
    query: str
    total_results: int
    items: List[SearchResultItem]

class SearchProvider(ABC):
    @abstractmethod
    async def search_global(
        self,
        query: str,
        organization_id: UUID,
        user_id: UUID,
        workspace_id: Optional[UUID] = None,
        limit: int = 20,
        offset: int = 0
    ) -> SearchResponse:
        pass

    @abstractmethod
    async def search_messages(
        self,
        query: str,
        organization_id: UUID,
        user_id: UUID,
        conversation_id: Optional[UUID] = None,
        limit: int = 20,
        offset: int = 0
    ) -> SearchResponse:
        pass

    @abstractmethod
    async def search_files(
        self,
        query: str,
        organization_id: UUID,
        user_id: UUID,
        mime_category: Optional[str] = None,
        limit: int = 20,
        offset: int = 0
    ) -> SearchResponse:
        pass

    @abstractmethod
    async def search_projects(
        self,
        query: str,
        organization_id: UUID,
        user_id: UUID,
        workspace_id: Optional[UUID] = None,
        limit: int = 20,
        offset: int = 0
    ) -> SearchResponse:
        pass

    @abstractmethod
    async def search_members(
        self,
        query: str,
        organization_id: UUID,
        user_id: UUID,
        limit: int = 20,
        offset: int = 0
    ) -> SearchResponse:
        pass

    @abstractmethod
    async def search_conversations(
        self,
        query: str,
        organization_id: UUID,
        user_id: UUID,
        limit: int = 20,
        offset: int = 0
    ) -> SearchResponse:
        pass
