from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, or_, and_
from uuid import UUID
from typing import Optional, List
from datetime import datetime
from .models import Document, DocumentUploadJob, Folder, DocumentFavorite, DocumentShare

class DocumentRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_document(self, doc_data: dict) -> Document:
        doc = Document(**doc_data)
        self.db.add(doc)
        await self.db.flush()
        return doc

    async def get_document(self, doc_id: UUID, include_deleted: bool = False) -> Optional[Document]:
        stmt = select(Document).where(Document.id == doc_id)
        if not include_deleted:
            stmt = stmt.where(Document.deleted_at.is_(None))
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_document_by_checksum(self, sha256: str, org_id: UUID, workspace_id: Optional[UUID] = None) -> Optional[Document]:
        stmt = select(Document).where(
            Document.checksum_sha256 == sha256,
            Document.organization_id == org_id,
            Document.deleted_at.is_(None)
        )
        if workspace_id:
            stmt = stmt.where(Document.workspace_id == workspace_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def list_documents(
        self,
        org_id: UUID,
        workspace_id: Optional[UUID] = None,
        project_id: Optional[UUID] = None,
        folder_id: Optional[UUID] = None,
        search_query: Optional[str] = None,
        file_type: Optional[str] = None,
        status_filter: Optional[str] = None,
        is_trash: bool = False,
        limit: int = 50,
        offset: int = 0
    ) -> List[Document]:
        stmt = select(Document).where(Document.organization_id == org_id)

        if is_trash:
            stmt = stmt.where(Document.deleted_at.isnot(None))
        else:
            stmt = stmt.where(Document.deleted_at.is_(None))

        if workspace_id:
            stmt = stmt.where(Document.workspace_id == workspace_id)
        if project_id:
            stmt = stmt.where(Document.project_id == project_id)
        if folder_id:
            stmt = stmt.where(Document.folder_id == folder_id)
        if status_filter:
            stmt = stmt.where(Document.processing_status == status_filter.upper())
        if file_type:
            stmt = stmt.where(or_(Document.extension == file_type.lower(), Document.mime_type.ilike(f"%{file_type}%")))
        if search_query:
            term = f"%{search_query}%"
            stmt = stmt.where(or_(
                Document.filename.ilike(term),
                Document.title.ilike(term),
                Document.original_filename.ilike(term)
            ))
        
        stmt = stmt.order_by(desc(Document.created_at)).limit(limit).offset(offset)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_recent_documents(self, org_id: UUID, user_id: Optional[UUID] = None, limit: int = 10) -> List[Document]:
        stmt = select(Document).where(
            Document.organization_id == org_id,
            Document.deleted_at.is_(None)
        )
        if user_id:
            stmt = stmt.where(Document.uploaded_by == user_id)
        stmt = stmt.order_by(desc(Document.updated_at)).limit(limit)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_favorite_documents(self, user_id: UUID, org_id: UUID, limit: int = 50) -> List[Document]:
        stmt = select(Document).join(DocumentFavorite, DocumentFavorite.document_id == Document.id).where(
            DocumentFavorite.user_id == user_id,
            Document.organization_id == org_id,
            Document.deleted_at.is_(None)
        ).order_by(desc(DocumentFavorite.created_at)).limit(limit)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def is_favorite(self, user_id: UUID, doc_id: UUID) -> bool:
        stmt = select(DocumentFavorite).where(
            DocumentFavorite.user_id == user_id,
            DocumentFavorite.document_id == doc_id
        )
        res = await self.db.execute(stmt)
        return res.scalar_one_or_none() is not None

    async def toggle_favorite(self, user_id: UUID, doc_id: UUID) -> bool:
        stmt = select(DocumentFavorite).where(
            DocumentFavorite.user_id == user_id,
            DocumentFavorite.document_id == doc_id
        )
        res = await self.db.execute(stmt)
        fav = res.scalar_one_or_none()
        if fav:
            await self.db.delete(fav)
            await self.db.flush()
            return False
        else:
            new_fav = DocumentFavorite(user_id=user_id, document_id=doc_id)
            self.db.add(new_fav)
            await self.db.flush()
            return True

    async def create_upload_job(self, job_data: dict) -> DocumentUploadJob:
        job = DocumentUploadJob(**job_data)
        self.db.add(job)
        await self.db.flush()
        return job

    async def get_upload_job(self, job_id: UUID) -> Optional[DocumentUploadJob]:
        stmt = select(DocumentUploadJob).where(DocumentUploadJob.id == job_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def delete_document(self, doc: Document) -> None:
        await self.db.delete(doc)
        await self.db.flush()

