import logging
from uuid import UUID
from typing import Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.documents.models import Document
from app.workspace.models import Workspace
from app.projects.models import Project

logger = logging.getLogger(__name__)

class CitationResolver:
    @staticmethod
    async def resolve_source_metadata(
        db: AsyncSession,
        document_id: UUID
    ) -> Optional[Dict[str, Any]]:
        """Resolves rich source metadata for a document ID from the database."""
        try:
            # 1. Fetch document details
            doc_stmt = select(Document).where(Document.id == document_id)
            doc_res = await db.execute(doc_stmt)
            doc = doc_res.scalar_one_or_none()
            
            if not doc:
                return None
                
            # 2. Fetch workspace name
            ws_stmt = select(Workspace.name).where(Workspace.id == doc.workspace_id)
            ws_res = await db.execute(ws_stmt)
            ws_name = ws_res.scalar() or "Unknown Workspace"
            
            # 3. Fetch project name
            proj_stmt = select(Project.name).where(Project.id == doc.project_id)
            proj_res = await db.execute(proj_stmt)
            proj_name = proj_res.scalar() or "Unknown Project"
            
            return {
                "document": doc.filename,
                "document_id": doc.id,
                "version": doc.version,
                "workspace": ws_name,
                "project": proj_name
            }
        except Exception as e:
            logger.error(f"Error resolving source metadata for doc {document_id}: {str(e)}")
            return None
