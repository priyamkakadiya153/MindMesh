from typing import Dict, Any, Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from .models import Document
from ..processing.models import DocumentContent
from ..storage.factory import StorageProviderFactory

class DocumentPreviewService:
    @staticmethod
    async def generate_preview(db: AsyncSession, document: Document) -> Dict[str, Any]:
        """Generates structured preview data for PDF, text, code, images, and office documents."""
        ext = (document.extension or "").lower().replace(".", "")
        mime = (document.mime_type or "").lower()

        # Check if text content has been extracted in DocumentContent table
        stmt = select(DocumentContent).where(DocumentContent.document_id == document.id)
        res = await db.execute(stmt)
        content_rec = res.scalar_one_or_none()

        extracted_text = content_rec.extracted_text if content_rec else ""
        content_json = content_rec.content_json if content_rec else {}

        # 1. Images
        if mime.startswith("image/") or ext in ["png", "jpg", "jpeg", "gif", "webp"]:
            return {
                "preview_type": "image",
                "document_id": str(document.id),
                "title": document.title or document.filename,
                "mime_type": document.mime_type,
                "download_url": f"/api/v1/documents/{document.id}/download",
                "metadata": {
                    "size_bytes": document.size,
                    "dimensions": content_json.get("metadata", {})
                }
            }

        # 2. Code files & Structured text
        code_exts = ["java", "py", "js", "ts", "c", "cpp", "html", "css", "json", "xml", "yaml", "yml", "sql"]
        if ext in code_exts or "javascript" in mime or "json" in mime or "xml" in mime:
            snippet = extracted_text if extracted_text else "# Preview unavailable - extract content first"
            return {
                "preview_type": "code",
                "language": ext,
                "document_id": str(document.id),
                "title": document.title or document.filename,
                "text": snippet[:20000], # return up to 20k characters for web editor preview
                "line_count": len(snippet.splitlines()),
                "size_bytes": document.size
            }

        # 3. Text & Markdown & CSV & RTF
        if ext in ["txt", "md", "csv", "rtf"] or mime.startswith("text/"):
            return {
                "preview_type": "text",
                "document_id": str(document.id),
                "title": document.title or document.filename,
                "text": extracted_text[:20000] if extracted_text else "No text extracted.",
                "size_bytes": document.size
            }

        # 4. PDF
        if ext == "pdf" or mime == "application/pdf":
            return {
                "preview_type": "pdf",
                "document_id": str(document.id),
                "title": document.title or document.filename,
                "download_url": f"/api/v1/documents/{document.id}/download",
                "text_summary": extracted_text[:2000] if extracted_text else "",
                "page_count": content_json.get("statistics", {}).get("page_count", 1)
            }

        # 5. Office Documents / Presentations / Spreadsheets / Archives (Metadata & extracted summary fallback)
        return {
            "preview_type": "metadata",
            "document_id": str(document.id),
            "title": document.title or document.filename,
            "filename": document.filename,
            "original_filename": document.original_filename,
            "mime_type": document.mime_type,
            "extension": document.extension,
            "size_bytes": document.size,
            "version": document.version,
            "download_url": f"/api/v1/documents/{document.id}/download",
            "extracted_text_snippet": extracted_text[:1000] if extracted_text else "Preview rendering not supported natively. Download to view complete file."
        }
