from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from typing import Optional
from datetime import datetime, time
from sqlalchemy import select, func
from ..models.workspace import Workspace
from ..projects.models import Project
from ..models.document import Document
from ..models.attachments import Attachment
from ..models.chat import Chat
from ..models.user import User
from ..models.message import Message
from ..ai.embeddings.models import DocumentChunk

import asyncio

class DashboardAggregator:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def _exec_scalar(self, stmt):
        res = await self.db.execute(stmt)
        return res.scalar() or 0

    async def aggregate_stats(self, org_id: UUID, workspace_id: Optional[UUID] = None) -> dict:
        ws_count_stmt = select(func.count(Workspace.id)).where(Workspace.organization_id == org_id, Workspace.is_active == True)

        projects_stmt = select(func.count(Project.id)).where(Project.organization_id == org_id, Project.is_active == True)
        if workspace_id:
            projects_stmt = projects_stmt.where(Project.workspace_id == workspace_id)

        projects_indexed_stmt = (
            select(func.count(func.distinct(Project.id)))
            .join(Document, Document.project_id == Project.id)
            .where(
                Project.organization_id == org_id,
                Project.is_active == True,
                Document.processing_status.in_(["COMPLETED", "INDEXED"])
            )
        )
        if workspace_id:
            projects_indexed_stmt = projects_indexed_stmt.where(Project.workspace_id == workspace_id)

        documents_stmt = select(func.count(Document.id)).where(Document.organization_id == org_id, Document.is_active == True)
        if workspace_id:
            documents_stmt = documents_stmt.where(Document.workspace_id == workspace_id)

        attachments_stmt = select(func.count(Attachment.id)).where(Attachment.organization_id == org_id, Attachment.status == "active", Attachment.is_active == True)
        if workspace_id:
            attachments_stmt = attachments_stmt.where(Attachment.workspace_id == workspace_id)

        documents_indexed_stmt = select(func.count(Document.id)).where(
            Document.organization_id == org_id,
            Document.is_active == True,
            Document.processing_status.in_(["COMPLETED", "INDEXED"])
        )
        if workspace_id:
            documents_indexed_stmt = documents_indexed_stmt.where(Document.workspace_id == workspace_id)

        chunks_stmt = (
            select(func.count(DocumentChunk.id))
            .join(Document, Document.id == DocumentChunk.document_id)
            .where(Document.organization_id == org_id, Document.is_active == True)
        )
        if workspace_id:
            chunks_stmt = chunks_stmt.where(Document.workspace_id == workspace_id)

        chats_stmt = select(func.count(Chat.id)).where(Chat.organization_id == org_id, Chat.is_active == True)
        if workspace_id:
            chats_stmt = chats_stmt.where(Chat.workspace_id == workspace_id)

        today_start = datetime.combine(datetime.utcnow().date(), time.min)
        messages_today_stmt = select(func.count(Message.id)).where(
            Message.organization_id == org_id,
            Message.created_at >= today_start
        )

        storage_stmt = select(func.sum(Document.size)).where(Document.organization_id == org_id, Document.is_active == True)
        if workspace_id:
            storage_stmt = storage_stmt.where(Document.workspace_id == workspace_id)

        att_storage_stmt = select(func.sum(Attachment.file_size)).where(Attachment.organization_id == org_id, Attachment.status == "active", Attachment.is_active == True)
        if workspace_id:
            att_storage_stmt = att_storage_stmt.where(Attachment.workspace_id == workspace_id)

        if workspace_id:
            from ..workspace.models import WorkspaceMember
            members_stmt = select(func.count(WorkspaceMember.id)).where(WorkspaceMember.workspace_id == workspace_id, WorkspaceMember.is_active == True)
        else:
            from ..models.organization_member import OrganizationMember
            members_stmt = select(func.count(OrganizationMember.id)).where(OrganizationMember.organization_id == org_id, OrganizationMember.is_active == True)

        workspaces_count = await self._exec_scalar(ws_count_stmt)
        projects_count = await self._exec_scalar(projects_stmt)
        projects_indexed_count = await self._exec_scalar(projects_indexed_stmt)
        documents_count = await self._exec_scalar(documents_stmt)
        attachments_count = await self._exec_scalar(attachments_stmt)
        doc_indexed_raw = await self._exec_scalar(documents_indexed_stmt)
        chunks_count = await self._exec_scalar(chunks_stmt)
        chats_count = await self._exec_scalar(chats_stmt)
        messages_today_count = await self._exec_scalar(messages_today_stmt)
        storage_used = await self._exec_scalar(storage_stmt)
        att_storage_used = await self._exec_scalar(att_storage_stmt)
        members_count = await self._exec_scalar(members_stmt)

        total_documents_count = documents_count + attachments_count
        documents_indexed_count = doc_indexed_raw + attachments_count
        total_storage_used = int(storage_used) + int(att_storage_used)

        if total_documents_count == 0:
            indexing_status = "EMPTY"
        elif documents_indexed_count == total_documents_count:
            indexing_status = "COMPLETED"
        else:
            indexing_status = "PENDING"

        return {
            "workspaces_count": workspaces_count,
            "projects_count": projects_count,
            "projects_indexed_count": projects_indexed_count,
            "projects_pending_count": max(0, projects_count - projects_indexed_count),
            "documents_count": total_documents_count,
            "documents_indexed_count": documents_indexed_count,
            "chunks_count": chunks_count,
            "chats_count": chats_count,
            "messages_today_count": messages_today_count,
            "storage_used": total_storage_used,
            "members_count": members_count,
            "indexing_status": indexing_status
        }


