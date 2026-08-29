import hashlib
from uuid import UUID, uuid4
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from ..documents.models import Document, DocumentVersion
from ..documents.exceptions import DocumentNotFoundException, InvalidFileException
from ..documents.audit import AuditLogger
from ..storage.factory import StorageProviderFactory

class VersionService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.audit = AuditLogger(db)

    async def list_versions(self, document_id: UUID) -> List[DocumentVersion]:
        stmt = select(DocumentVersion).where(DocumentVersion.document_id == document_id).order_by(DocumentVersion.version_number)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def create_version(
        self,
        document_id: UUID,
        file_content: bytes,
        filename: str,
        content_type: str,
        user_id: UUID,
        change_summary: str
    ) -> Document:
        stmt = select(Document).where(Document.id == document_id, Document.is_active == True)
        doc = (await self.db.execute(stmt)).scalar_one_or_none()
        if not doc:
            raise DocumentNotFoundException(str(document_id))

        checksum = hashlib.sha256(file_content).hexdigest()
        file_size = len(file_content)

        # Before writing, let's create a snapshot of the current version if it's the first update
        existing_versions = await self.list_versions(document_id)
        if len(existing_versions) == 0:
            # Seed the initial version v1 record
            initial_v = DocumentVersion(
                document_id=document_id,
                version_number=doc.version,
                storage_path=doc.storage_path,
                checksum_sha256=doc.checksum_sha256,
                file_size=doc.size,
                uploaded_by=doc.uploaded_by,
                change_summary="Initial Upload"
            )
            self.db.add(initial_v)
            await self.db.flush()

        # Save new file to storage
        ext = filename.split(".")[-1].lower() if "." in filename else "bin"
        storage_filename = f"{uuid4()}.{ext}"
        storage_path = f"{doc.organization_id}/{doc.workspace_id}/{doc.project_id}/{storage_filename}"
        
        provider = StorageProviderFactory.get_provider()
        await provider.save(file_content, storage_path)

        new_version_number = doc.version + 1

        # Create new version record
        new_v = DocumentVersion(
            document_id=document_id,
            version_number=new_version_number,
            storage_path=storage_path,
            checksum_sha256=checksum,
            file_size=file_size,
            uploaded_by=user_id,
            change_summary=change_summary
        )
        self.db.add(new_v)

        # Update Document pointers
        doc.version = new_version_number
        doc.storage_path = storage_path
        doc.checksum_sha256 = checksum
        doc.size = file_size
        doc.filename = filename

        await self.audit.log_action(
            document_id=document_id,
            user_id=user_id,
            action="VERSION_CREATED",
            metadata={"version_number": new_version_number, "change_summary": change_summary}
        )

        await self.db.commit()
        return doc

    async def restore_version(
        self,
        document_id: UUID,
        version_number: int,
        user_id: UUID
    ) -> Document:
        stmt = select(Document).where(Document.id == document_id, Document.is_active == True)
        doc = (await self.db.execute(stmt)).scalar_one_or_none()
        if not doc:
            raise DocumentNotFoundException(str(document_id))

        stmt_v = select(DocumentVersion).where(
            DocumentVersion.document_id == document_id,
            DocumentVersion.version_number == version_number
        )
        ver = (await self.db.execute(stmt_v)).scalar_one_or_none()
        if not ver:
            raise InvalidFileException(f"Version number {version_number} was not found for this document.")

        new_version_number = doc.version + 1

        # Restoring creates a copy as a new version number (Immutable history!)
        restored_v = DocumentVersion(
            document_id=document_id,
            version_number=new_version_number,
            storage_path=ver.storage_path,
            checksum_sha256=ver.checksum_sha256,
            file_size=ver.file_size,
            uploaded_by=user_id,
            change_summary=f"Restored from version {version_number}"
        )
        self.db.add(restored_v)

        # Update Document pointers
        doc.version = new_version_number
        doc.storage_path = ver.storage_path
        doc.checksum_sha256 = ver.checksum_sha256
        doc.size = ver.file_size

        await self.audit.log_action(
            document_id=document_id,
            user_id=user_id,
            action="RESTORE",
            metadata={"restored_from": version_number, "new_version_number": new_version_number}
        )

        await self.db.commit()
        return doc
