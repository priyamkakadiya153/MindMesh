from uuid import UUID

class ChunkMetadataBuilder:
    @staticmethod
    def build_metadata(
        doc_rec: any,
        heading: str = None,
        page: int = None,
        custom: dict = None
    ) -> dict:
        """Assembles standard audit metadata structure for a document chunk."""
        meta = {
            "organization_id": str(doc_rec.organization_id),
            "workspace_id": str(doc_rec.workspace_id),
            "project_id": str(doc_rec.project_id),
            "document_id": str(doc_rec.id),
            "filename": doc_rec.filename,
            "heading": heading or "General",
            "page": page or 1
        }
        if custom:
            meta.update(custom)
        return meta
