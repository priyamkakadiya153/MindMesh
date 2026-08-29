from uuid import UUID
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from ..documents.models import Document, DocumentMetadata
from ..documents.exceptions import DocumentNotFoundException, InvalidFileException
from ..documents.audit import AuditLogger

class MetadataService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.audit = AuditLogger(db)

    async def get_metadata(self, document_id: UUID) -> DocumentMetadata:
        stmt = select(DocumentMetadata).where(DocumentMetadata.document_id == document_id)
        result = await self.db.execute(stmt)
        metadata = result.scalar_one_or_none()
        
        if not metadata:
            # Lazy initialize empty metadata if missing
            stmt_doc = select(Document).where(Document.id == document_id)
            doc = (await self.db.execute(stmt_doc)).scalar_one_or_none()
            if not doc:
                raise DocumentNotFoundException(str(document_id))
            
            metadata = DocumentMetadata(
                document_id=document_id,
                title=doc.filename,
                confidentiality="internal"
            )
            self.db.add(metadata)
            await self.db.flush()
        
        return metadata

    async def update_metadata(
        self,
        document_id: UUID,
        user_id: UUID,
        update_data: dict
    ) -> DocumentMetadata:
        metadata = await self.get_metadata(document_id)
        
        # Validation checks
        title = update_data.get("title")
        if title is not None:
            if not title.strip():
                raise InvalidFileException("Title cannot be empty.")
            metadata.title = title

        if "description" in update_data:
            metadata.description = update_data["description"]
        if "author" in update_data:
            metadata.author = update_data["author"]
        if "language" in update_data:
            metadata.language = update_data["language"]
        if "keywords" in update_data:
            metadata.keywords = update_data["keywords"]
        if "labels" in update_data:
            metadata.labels = update_data["labels"]
        if "categories" in update_data:
            metadata.categories = update_data["categories"]
        if "department" in update_data:
            metadata.department = update_data["department"]
        if "business_unit" in update_data:
            metadata.business_unit = update_data["business_unit"]
        
        conf = update_data.get("confidentiality")
        if conf is not None:
            if conf not in ["public", "internal", "confidential", "restricted"]:
                raise InvalidFileException("Invalid confidentiality level.")
            metadata.confidentiality = conf
            
        if "custom_metadata" in update_data:
            metadata.custom_metadata = update_data["custom_metadata"]

        await self.audit.log_action(
            document_id=document_id,
            user_id=user_id,
            action="METADATA_UPDATED",
            metadata={"updated_fields": list(update_data.keys())}
        )
        
        await self.db.commit()
        return metadata
