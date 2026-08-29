from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_, and_, desc, func
from typing import List, Optional
from uuid import UUID
from datetime import datetime

from .base import SearchProvider, SearchResponse, SearchResultItem
from ..models.conversations import Conversation, ConversationMember, DirectMessage
from ..models.attachments import Attachment
from ..models.user import User
from ..projects.models import Project
from ..models.organization_member import OrganizationMember

class PostgresSearchProvider(SearchProvider):
    def __init__(self, db: AsyncSession):
        self.db = db

    async def search_global(
        self,
        query: str,
        organization_id: UUID,
        user_id: UUID,
        workspace_id: Optional[UUID] = None,
        limit: int = 20,
        offset: int = 0
    ) -> SearchResponse:
        items: List[SearchResultItem] = []
        pattern = f"%{query}%"

        # 1. Search Messages in user's conversations
        conv_stmt = select(ConversationMember.conversation_id).where(ConversationMember.user_id == user_id)
        user_conv_ids = (await self.db.execute(conv_stmt)).scalars().all()

        if user_conv_ids:
            msg_stmt = select(DirectMessage, User).join(
                User, DirectMessage.sender_id == User.id
            ).where(
                DirectMessage.organization_id == organization_id,
                DirectMessage.conversation_id.in_(user_conv_ids),
                DirectMessage.content.ilike(pattern),
                DirectMessage.deleted == False
            ).limit(limit)

            msg_rows = (await self.db.execute(msg_stmt)).all()
            for msg, sender in msg_rows:
                items.append(SearchResultItem(
                    id=msg.id,
                    type="message",
                    title=f"Message by {sender.full_name}",
                    snippet=msg.content[:150],
                    location="Conversation",
                    author_name=sender.full_name,
                    created_at=msg.created_at
                ))

        # 2. Search Files
        file_stmt = select(Attachment, User).join(
            User, Attachment.uploaded_by == User.id
        ).where(
            Attachment.organization_id == organization_id,
            Attachment.original_filename.ilike(pattern),
            Attachment.deleted_at == None
        ).limit(limit)

        file_rows = (await self.db.execute(file_stmt)).all()
        for att, uploader in file_rows:
            items.append(SearchResultItem(
                id=att.id,
                type="file",
                title=att.original_filename,
                snippet=f"File ({att.mime_type}, {(att.file_size/1024):.1f} KB)",
                location="Shared Files",
                author_name=uploader.full_name,
                created_at=att.created_at
            ))

        # 3. Search Projects
        proj_stmt = select(Project).where(
            Project.organization_id == organization_id,
            or_(Project.name.ilike(pattern), Project.description.ilike(pattern))
        ).limit(limit)

        proj_rows = (await self.db.execute(proj_stmt)).scalars().all()
        for proj in proj_rows:
            items.append(SearchResultItem(
                id=proj.id,
                type="project",
                title=proj.name,
                snippet=proj.description or "Project",
                location="Projects",
                created_at=proj.created_at
            ))

        # 4. Search Members
        mem_stmt = select(User).join(
            OrganizationMember, OrganizationMember.user_id == User.id
        ).where(
            OrganizationMember.organization_id == organization_id,
            or_(User.first_name.ilike(pattern), User.last_name.ilike(pattern), User.email.ilike(pattern))
        ).limit(limit)

        mem_rows = (await self.db.execute(mem_stmt)).scalars().all()
        for u in mem_rows:
            items.append(SearchResultItem(
                id=u.id,
                type="member",
                title=u.full_name,
                snippet=u.email,
                location="Directory",
                created_at=u.created_at
            ))

        # 5. Search Documents & In-Document Content
        try:
            from ..documents.models import Document
            from ..ai.embeddings.models import DocumentChunk
            from ..processing.models import DocumentContent

            chunk_doc_ids_stmt = select(DocumentChunk.document_id).where(
                DocumentChunk.content.ilike(pattern),
                DocumentChunk.deleted_at.is_(None)
            )
            content_doc_ids_stmt = select(DocumentContent.document_id).where(
                DocumentContent.extracted_text.ilike(pattern)
            )

            doc_stmt = select(Document, User).join(
                User, Document.uploaded_by == User.id, isouter=True
            ).where(
                Document.organization_id == organization_id,
                Document.deleted_at == None,
                or_(
                    Document.title.ilike(pattern),
                    Document.filename.ilike(pattern),
                    Document.original_filename.ilike(pattern),
                    Document.id.in_(chunk_doc_ids_stmt),
                    Document.id.in_(content_doc_ids_stmt)
                )
            )
            if workspace_id:
                doc_stmt = doc_stmt.where(Document.workspace_id == workspace_id)
            doc_stmt = doc_stmt.limit(limit)

            doc_rows = (await self.db.execute(doc_stmt)).all()
            for doc, uploader in doc_rows:
                author_name = uploader.full_name if uploader else "System"
                doc_title = doc.title or doc.original_filename or doc.filename or "Document"
                snippet = f"Document ({doc.mime_type or 'file'}, {(doc.size/1024 if doc.size else 0):.1f} KB)"

                # If matching chunk text, extract surrounding snippet
                c_match_stmt = select(DocumentChunk.content).where(
                    DocumentChunk.document_id == doc.id,
                    DocumentChunk.content.ilike(pattern)
                ).limit(1)
                matching_chunk = (await self.db.execute(c_match_stmt)).scalar_one_or_none()
                if matching_chunk:
                    idx = matching_chunk.lower().find(query.lower())
                    if idx != -1:
                        start = max(0, idx - 40)
                        end = min(len(matching_chunk), idx + len(query) + 80)
                        snippet = ("..." if start > 0 else "") + matching_chunk[start:end].strip().replace("\n", " ") + ("..." if end < len(matching_chunk) else "")

                items.append(SearchResultItem(
                    id=doc.id,
                    type="document",
                    title=doc_title,
                    snippet=snippet,
                    location="Documents",
                    author_name=author_name,
                    created_at=doc.created_at
                ))
        except Exception as e:
            logger.warning(f"Error searching documents: {e}")

        items.sort(key=lambda x: x.created_at, reverse=True)
        return SearchResponse(query=query, total_results=len(items), items=items[offset:offset+limit])

    async def search_messages(
        self,
        query: str,
        organization_id: UUID,
        user_id: UUID,
        conversation_id: Optional[UUID] = None,
        limit: int = 20,
        offset: int = 0
    ) -> SearchResponse:
        pattern = f"%{query}%"
        conv_stmt = select(ConversationMember.conversation_id).where(ConversationMember.user_id == user_id)
        user_conv_ids = (await self.db.execute(conv_stmt)).scalars().all()

        if not user_conv_ids:
            return SearchResponse(query=query, total_results=0, items=[])

        stmt = select(DirectMessage, User).join(
            User, DirectMessage.sender_id == User.id
        ).where(
            DirectMessage.organization_id == organization_id,
            DirectMessage.conversation_id.in_(user_conv_ids),
            DirectMessage.content.ilike(pattern),
            DirectMessage.deleted == False
        )
        if conversation_id:
            stmt = stmt.where(DirectMessage.conversation_id == conversation_id)

        stmt = stmt.order_by(desc(DirectMessage.created_at)).offset(offset).limit(limit)
        rows = (await self.db.execute(stmt)).all()

        items = [
            SearchResultItem(
                id=msg.id,
                type="message",
                title=f"Message by {sender.full_name}",
                snippet=msg.content[:150],
                location="Conversation",
                author_name=sender.full_name,
                created_at=msg.created_at
            ) for msg, sender in rows
        ]

        return SearchResponse(query=query, total_results=len(items), items=items)

    async def search_files(
        self,
        query: str,
        organization_id: UUID,
        user_id: UUID,
        mime_category: Optional[str] = None,
        limit: int = 20,
        offset: int = 0
    ) -> SearchResponse:
        pattern = f"%{query}%"
        stmt = select(Attachment, User).join(
            User, Attachment.uploaded_by == User.id
        ).where(
            Attachment.organization_id == organization_id,
            Attachment.original_filename.ilike(pattern),
            Attachment.deleted_at == None
        )
        if mime_category:
            stmt = stmt.where(Attachment.mime_type.ilike(f"{mime_category}/%"))

        stmt = stmt.order_by(desc(Attachment.created_at)).offset(offset).limit(limit)
        rows = (await self.db.execute(stmt)).all()

        items = [
            SearchResultItem(
                id=att.id,
                type="file",
                title=att.original_filename,
                snippet=f"File ({att.mime_type}, {(att.file_size/1024):.1f} KB)",
                location="Shared Files",
                author_name=uploader.full_name,
                created_at=att.created_at
            ) for att, uploader in rows
        ]

        return SearchResponse(query=query, total_results=len(items), items=items)

    async def search_projects(
        self,
        query: str,
        organization_id: UUID,
        user_id: UUID,
        workspace_id: Optional[UUID] = None,
        limit: int = 20,
        offset: int = 0
    ) -> SearchResponse:
        pattern = f"%{query}%"
        stmt = select(Project).where(
            Project.organization_id == organization_id,
            or_(Project.name.ilike(pattern), Project.description.ilike(pattern))
        ).order_by(desc(Project.created_at)).offset(offset).limit(limit)

        rows = (await self.db.execute(stmt)).scalars().all()
        items = [
            SearchResultItem(
                id=proj.id,
                type="project",
                title=proj.name,
                snippet=proj.description or "Project",
                location="Projects",
                created_at=proj.created_at
            ) for proj in rows
        ]
        return SearchResponse(query=query, total_results=len(items), items=items)

    async def search_members(
        self,
        query: str,
        organization_id: UUID,
        user_id: UUID,
        limit: int = 20,
        offset: int = 0
    ) -> SearchResponse:
        pattern = f"%{query}%"
        stmt = select(User).join(
            OrganizationMember, OrganizationMember.user_id == User.id
        ).where(
            OrganizationMember.organization_id == organization_id,
            or_(User.first_name.ilike(pattern), User.last_name.ilike(pattern), User.email.ilike(pattern))
        ).order_by(User.first_name).offset(offset).limit(limit)

        rows = (await self.db.execute(stmt)).scalars().all()
        items = [
            SearchResultItem(
                id=u.id,
                type="member",
                title=u.full_name,
                snippet=u.email,
                location="Directory",
                created_at=u.created_at
            ) for u in rows
        ]
        return SearchResponse(query=query, total_results=len(items), items=items)

    async def search_conversations(
        self,
        query: str,
        organization_id: UUID,
        user_id: UUID,
        limit: int = 20,
        offset: int = 0
    ) -> SearchResponse:
        pattern = f"%{query}%"
        stmt = select(Conversation).join(
            ConversationMember, Conversation.id == ConversationMember.conversation_id
        ).where(
            Conversation.organization_id == organization_id,
            ConversationMember.user_id == user_id,
            Conversation.name.ilike(pattern)
        ).order_by(desc(Conversation.created_at)).offset(offset).limit(limit)

        rows = (await self.db.execute(stmt)).scalars().all()
        items = [
            SearchResultItem(
                id=c.id,
                type="conversation",
                title=c.name or "Conversation",
                snippet=f"{c.type.upper()} Conversation",
                location="Messaging",
                created_at=c.created_at
            ) for c in rows
        ]
        return SearchResponse(query=query, total_results=len(items), items=items)
