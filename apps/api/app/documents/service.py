import hashlib
import os
from datetime import datetime
from uuid import UUID, uuid4
from typing import Optional, List, Tuple, AsyncGenerator
from fastapi import BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

import logging
from .repository import DocumentRepository

logger = logging.getLogger(__name__)
from .models import Document, DocumentUploadJob, Folder, DocumentShare
from .enums import ProcessingStatus, DocumentVisibility
from .validators import validate_file_attributes, sanitize_filename
from .exceptions import DocumentNotFoundException
from ..storage.factory import StorageProviderFactory
from ..search.indexer import SearchIndexer

class DocumentService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = DocumentRepository(db)

    async def upload_document(
        self,
        file_content: bytes,
        filename: str,
        content_type: str,
        org_id: UUID,
        workspace_id: UUID,
        project_id: Optional[UUID] = None,
        folder_id: Optional[UUID] = None,
        user_id: Optional[UUID] = None,
        title: Optional[str] = None,
        visibility: str = "private",
        background_tasks: Optional[BackgroundTasks] = None
    ) -> Document:
        file_size = len(file_content)
        
        # 1. Validate file size, extension, MIME type & security checks
        validate_file_attributes(filename, file_size, content_type)
        
        clean_filename = sanitize_filename(filename)

        # 2. Compute SHA256 checksum
        checksum = hashlib.sha256(file_content).hexdigest()
        
        # Duplicate detection check within workspace
        existing_doc = await self.repo.get_document_by_checksum(checksum, org_id, workspace_id)
        if existing_doc:
            # Verify if chunks exist for existing document; if missing, trigger pipeline
            from ..ai.embeddings.models import DocumentChunk
            chunk_check = await self.db.execute(
                select(DocumentChunk.id).where(DocumentChunk.document_id == existing_doc.id).limit(1)
            )
            if not chunk_check.scalar_one_or_none():
                from ..processing.pipeline import ProcessingPipeline
                pipeline = ProcessingPipeline(self.db)
                await pipeline.process_document(existing_doc.id)
                await self.db.commit()
                await self.db.refresh(existing_doc)
            return existing_doc

        # 3. Determine file storage paths
        ext = clean_filename.split(".")[-1].lower() if "." in clean_filename else "bin"
        storage_filename = f"{uuid4()}.{ext}"
        storage_path = f"documents/{org_id}/{workspace_id}/{storage_filename}"
        
        # 4. Save to configured storage provider
        storage_provider = StorageProviderFactory.get_provider()
        await storage_provider.save(file_content, storage_path)
        
        # 5. Save Document metadata record
        doc_data = {
            "organization_id": org_id,
            "workspace_id": workspace_id,
            "project_id": project_id,
            "folder_id": folder_id,
            "uploaded_by": user_id,
            "title": title or clean_filename,
            "filename": clean_filename,
            "original_filename": clean_filename,
            "stored_filename": storage_filename,
            "mime_type": content_type,
            "extension": ext,
            "size": file_size,
            "checksum_sha256": checksum,
            "storage_provider": "local",
            "storage_path": storage_path,
            "processing_status": "PROCESSING",
            "visibility": visibility,
            "version": 1
        }
        doc = await self.repo.create_document(doc_data)
        
        # 6. Initialize Upload Job record
        job_data = {
            "document_id": doc.id,
            "status": "COMPLETED"
        }
        await self.repo.create_upload_job(job_data)
        
        try:
            await self.db.flush()
        except Exception as e:
            print("DEBUG service upload_document initial flush error:", e)
            import traceback
            traceback.print_exc()
            raise e

        # 7. Extract text content & index into Universal Search immediately
        extracted_text = ""
        try:
            from ..processing.pipeline import ProcessingPipeline
            from ..processing.models import DocumentContent
            pipeline = ProcessingPipeline(self.db)
            await pipeline.process_document(doc.id)
            
            cnt_stmt = select(DocumentContent).where(DocumentContent.document_id == doc.id)
            cnt_rec = (await self.db.execute(cnt_stmt)).scalar_one_or_none()
            extracted_text = cnt_rec.extracted_text if cnt_rec else ""
        except Exception as err:
            logger.warning(f"Error extracting document text: {err}")
            extracted_text = ""

        try:
            await SearchIndexer.index_entity(
                db=self.db,
                entity_type="document",
                entity_id=doc.id,
                title=doc.title or doc.filename,
                content=f"{doc.filename}\n{extracted_text}".strip(),
                workspace_id=doc.workspace_id,
                organization_id=doc.organization_id,
                owner_id=doc.uploaded_by,
                tags=[doc.extension, "document"],
                metadata_json={
                    "mime_type": doc.mime_type,
                    "extension": doc.extension,
                    "size_bytes": doc.size,
                    "status": doc.processing_status
                }
            )
        except Exception:
            pass

        await self.db.commit()
        await self.db.refresh(doc)
        return doc

    async def get_document(self, doc_id: UUID, include_deleted: bool = False) -> Document:
        doc = await self.repo.get_document(doc_id, include_deleted=include_deleted)
        if not doc:
            raise DocumentNotFoundException(str(doc_id))
        return doc

    async def update_document(
        self,
        doc_id: UUID,
        title: Optional[str] = None,
        folder_id: Optional[UUID] = None,
        visibility: Optional[str] = None,
        project_id: Optional[UUID] = None
    ) -> Document:
        doc = await self.get_document(doc_id)
        if title is not None:
            doc.title = title
        if folder_id is not None:
            doc.folder_id = folder_id
        if visibility is not None:
            doc.visibility = visibility
        if project_id is not None:
            doc.project_id = project_id
        doc.updated_at = datetime.utcnow()
        await self.db.commit()
        await self.db.refresh(doc)

        # Update search index
        try:
            await SearchIndexer.index_entity(
                db=self.db,
                entity_type="document",
                entity_id=doc.id,
                title=doc.title or doc.filename,
                content=f"Document filename: {doc.filename}",
                workspace_id=doc.workspace_id,
                organization_id=doc.organization_id,
                owner_id=doc.uploaded_by,
                tags=[doc.extension, "document"],
                metadata_json={"mime_type": doc.mime_type, "extension": doc.extension, "size_bytes": doc.size}
            )
        except Exception:
            pass

        return doc

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
        return await self.repo.list_documents(
            org_id=org_id,
            workspace_id=workspace_id,
            project_id=project_id,
            folder_id=folder_id,
            search_query=search_query,
            file_type=file_type,
            status_filter=status_filter,
            is_trash=is_trash,
            limit=limit,
            offset=offset
        )

    async def get_recent_documents(self, org_id: UUID, user_id: Optional[UUID] = None, limit: int = 10) -> List[Document]:
        return await self.repo.get_recent_documents(org_id=org_id, user_id=user_id, limit=limit)

    async def get_favorite_documents(self, user_id: UUID, org_id: UUID, limit: int = 50) -> List[Document]:
        return await self.repo.get_favorite_documents(user_id=user_id, org_id=org_id, limit=limit)

    async def toggle_favorite(self, user_id: UUID, doc_id: UUID) -> bool:
        doc = await self.get_document(doc_id)
        res = await self.repo.toggle_favorite(user_id, doc.id)
        await self.db.commit()
        return res

    async def share_document(self, doc_id: UUID, shared_with_user_id: UUID, permission_level: str = "read") -> DocumentShare:
        doc = await self.get_document(doc_id)
        stmt = select(DocumentShare).where(
            DocumentShare.document_id == doc_id,
            DocumentShare.shared_with_user_id == shared_with_user_id
        )
        res = await self.db.execute(stmt)
        share = res.scalar_one_or_none()
        if share:
            share.permission_level = permission_level
        else:
            share = DocumentShare(
                document_id=doc_id,
                shared_with_user_id=shared_with_user_id,
                permission_level=permission_level
            )
            self.db.add(share)
        doc.visibility = "shared"
        await self.db.commit()
        return share

    async def soft_delete_document(self, doc_id: UUID) -> bool:
        doc = await self.get_document(doc_id, include_deleted=True)
        doc.deleted_at = datetime.utcnow()
        doc.is_active = False
        await self.db.commit()

        # Remove from search index
        try:
            await SearchIndexer.delete_entity(self.db, "document", doc.id)
        except Exception:
            pass

        return True

    async def permanent_delete_document(self, doc_id: UUID) -> bool:
        doc = await self.get_document(doc_id, include_deleted=True)
        
        # Remove physical file from storage
        if doc.storage_path:
            try:
                provider = StorageProviderFactory.get_provider()
                provider.delete(doc.storage_path)
            except Exception as e:
                logger.warning(f"Failed to delete storage file {doc.storage_path}: {e}")

        # Remove search index entries
        try:
            await SearchIndexer.delete_entity(self.db, "document", doc.id)
        except Exception as e:
            logger.warning(f"Failed to delete search index entry: {e}")

        # Permanently delete document record from DB (cascades to all child relations)
        await self.repo.delete_document(doc)
        await self.db.commit()
        return True

    async def restore_document(self, doc_id: UUID) -> Document:
        doc = await self.get_document(doc_id, include_deleted=True)
        doc.deleted_at = None
        doc.is_active = True
        if doc.processing_status == ProcessingStatus.ARCHIVED:
            doc.processing_status = ProcessingStatus.READY
        await self.db.commit()
        await self.db.refresh(doc)

        # Re-index in search
        try:
            await SearchIndexer.index_entity(
                db=self.db,
                entity_type="document",
                entity_id=doc.id,
                title=doc.title or doc.filename,
                content=f"Restored document: {doc.filename}",
                workspace_id=doc.workspace_id,
                organization_id=doc.organization_id,
                owner_id=doc.uploaded_by,
                tags=[doc.extension, "document"]
            )
        except Exception:
            pass

        return doc

    async def get_document_stream(self, doc_id: UUID) -> Tuple[AsyncGenerator[bytes, None], Document]:
        doc = await self.get_document(doc_id)
        provider = StorageProviderFactory.get_provider()
        stream_gen = provider.stream(doc.storage_path)
        return stream_gen, doc

def settings_provider_name() -> str:
    from ..core.config import settings
    return settings.STORAGE_PROVIDER.lower()

