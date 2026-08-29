import logging
from uuid import UUID
from typing import List, Set
from sqlalchemy.ext.asyncio import AsyncSession
from ..context.validator import ContextSecurityValidator

logger = logging.getLogger(__name__)

class CitationValidator:
    @staticmethod
    async def validate_citation_permissions(
        db: AsyncSession,
        user_id: UUID,
        org_id: UUID,
        document_ids: List[UUID]
    ) -> bool:
        """Enforces permission checks on citations, ensuring the user can access all cited files."""
        if not document_ids:
            return True
            
        doc_set = set(document_ids)
        return await ContextSecurityValidator.validate_context_permissions(
            db=db,
            user_id=user_id,
            org_id=org_id,
            document_ids=doc_set
        )
