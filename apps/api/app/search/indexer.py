import logging
from typing import Optional, Dict, Any, List
from uuid import UUID
from datetime import datetime
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.search import SearchIndex
from ..models.document import Document
from ..models.task import Task
from ..models.user import User
from ..workspace.models import Workspace
from ..projects.models import Project
from ..knowledge.models import KnowledgeEntry
from ..automation.approval.models import WorkflowDefinition
from ..models.organization import Organization

logger = logging.getLogger(__name__)

class SearchIndexer:
    """Central search indexer and entity sync service.

    Updates or removes records in `search_index` when domain entities change.

    Includes automatic seeding to sync existing database entities into `search_index`.

    """

    @staticmethod
    async def index_entity(
        db: AsyncSession,
        entity_type: str,
        entity_id: UUID,
        title: str,
        content: Optional[str] = None,
        workspace_id: Optional[UUID] = None,
        organization_id: Optional[UUID] = None,
        owner_id: Optional[UUID] = None,
        tags: Optional[List[str]] = None,
        metadata_json: Optional[Dict[str, Any]] = None,
    ) -> SearchIndex:
        stmt = select(SearchIndex).where(
            SearchIndex.entity_type == entity_type.lower(),
            SearchIndex.entity_id == entity_id
        )
        res = await db.execute(stmt)
        record = res.scalar_one_or_none()

        if not record:
            record = SearchIndex(
                entity_type=entity_type.lower(),
                entity_id=entity_id,
                workspace_id=workspace_id,
                organization_id=organization_id,
                owner_id=owner_id,
                title=title,
                content=content or "",
                tags=tags or [],
                metadata_json=metadata_json or {},
            )
            db.add(record)
        else:
            record.title = title
            record.content = content or ""
            record.workspace_id = workspace_id
            record.organization_id = organization_id
            record.owner_id = owner_id
            record.tags = tags or []
            record.metadata_json = metadata_json or {}
            record.updated_at = datetime.utcnow()

        await db.flush()
        return record

    @staticmethod
    async def delete_entity(
        db: AsyncSession,
        entity_type: str,
        entity_id: UUID
    ) -> bool:
        stmt = delete(SearchIndex).where(
            SearchIndex.entity_type == entity_type.lower(),
            SearchIndex.entity_id == entity_id
        )
        res = await db.execute(stmt)
        await db.flush()
        return res.rowcount > 0

    @staticmethod
    async def auto_seed_index(db: AsyncSession) -> int:
        """Inspects core domain tables (Documents, Projects, Tasks, Knowledge, Users, Workflows, Workspaces)

        and ensures all existing entities are indexed in `search_index`.

        """
        indexed_count = 0

        # 1. Documents
        try:
            doc_stmt = select(Document)
            docs = (await db.execute(doc_stmt)).scalars().all()
            for doc in docs:
                title = getattr(doc, 'original_filename', None) or getattr(doc, 'filename', None) or getattr(doc, 'title', 'Untitled Document')
                desc = getattr(doc, 'description', '') or getattr(doc, 'original_filename', '') or ''
                await SearchIndexer.index_entity(
                    db=db,
                    entity_type="document",
                    entity_id=doc.id,
                    title=title,
                    content=desc,
                    workspace_id=getattr(doc, 'workspace_id', None),
                    organization_id=getattr(doc, 'organization_id', None),
                    owner_id=getattr(doc, 'uploaded_by', None) or getattr(doc, 'created_by', None),
                    tags=getattr(doc, 'tags', []) or ["document"],
                    metadata_json={
                        "file_type": getattr(doc, 'file_type', None),
                        "file_size": getattr(doc, 'file_size', None),
                        "status": getattr(doc, 'status', 'active')
                    }
                )
                indexed_count += 1
        except Exception as e:
            logger.warning(f"Error seeding documents into search index: {e}")

        # 2. Projects
        try:
            proj_stmt = select(Project)
            projs = (await db.execute(proj_stmt)).scalars().all()
            for proj in projs:
                await SearchIndexer.index_entity(
                    db=db,
                    entity_type="project",
                    entity_id=proj.id,
                    title=proj.name,
                    content=getattr(proj, 'description', '') or f"Project slug: {getattr(proj, 'slug', '')}",
                    workspace_id=getattr(proj, 'workspace_id', None),
                    organization_id=getattr(proj, 'organization_id', None),
                    owner_id=getattr(proj, 'created_by', None),
                    tags=["project"],
                    metadata_json={"status": getattr(proj, 'status', 'active')}
                )
                indexed_count += 1
        except Exception as e:
            logger.warning(f"Error seeding projects into search index: {e}")

        # 3. Tasks
        try:
            task_stmt = select(Task)
            tasks = (await db.execute(task_stmt)).scalars().all()
            for t in tasks:
                title = getattr(t, 'title', None) or (t.description[:60] if t.description else "Task Item")
                await SearchIndexer.index_entity(
                    db=db,
                    entity_type="task",
                    entity_id=t.id,
                    title=title,
                    content=t.description or "",
                    workspace_id=getattr(t, 'workspace_id', None),
                    organization_id=getattr(t, 'organization_id', None),
                    owner_id=getattr(t, 'assignee_id', None) or getattr(t, 'creator_id', None),
                    tags=["task"],
                    metadata_json={"status": getattr(t, 'status', 'open'), "priority": getattr(t, 'priority', 'medium')}
                )
                indexed_count += 1

        except Exception as e:
            logger.warning(f"Error seeding tasks into search index: {e}")

        # 4. Users
        try:
            user_stmt = select(User)
            users = (await db.execute(user_stmt)).scalars().all()
            for u in users:
                display_name = f"{getattr(u, 'full_name', '')} ({u.email})" if getattr(u, 'full_name', None) else u.email
                await SearchIndexer.index_entity(
                    db=db,
                    entity_type="user",
                    entity_id=u.id,
                    title=display_name,
                    content=f"User account for {u.email}",
                    workspace_id=None,
                    organization_id=None,
                    owner_id=u.id,
                    tags=["user", "member"],
                    metadata_json={"email": u.email, "role": getattr(u, 'role', 'user')}
                )
                indexed_count += 1
        except Exception as e:
            logger.warning(f"Error seeding users into search index: {e}")

        # 5. Knowledge Entries
        try:
            k_stmt = select(KnowledgeEntry)
            k_entries = (await db.execute(k_stmt)).scalars().all()
            for k in k_entries:
                await SearchIndexer.index_entity(
                    db=db,
                    entity_type="knowledge",
                    entity_id=k.id,
                    title=getattr(k, 'title', 'Knowledge Entry'),
                    content=getattr(k, 'content', '') or getattr(k, 'summary', ''),
                    workspace_id=getattr(k, 'workspace_id', None),
                    organization_id=getattr(k, 'organization_id', None),
                    owner_id=getattr(k, 'created_by', None),
                    tags=getattr(k, 'tags', []) or ["knowledge"],
                    metadata_json={"category": getattr(k, 'category', 'general')}
                )
                indexed_count += 1
        except Exception as e:
            logger.warning(f"Error seeding knowledge entries into search index: {e}")

        # 6. Workflows
        try:
            wf_stmt = select(WorkflowDefinition)
            wfs = (await db.execute(wf_stmt)).scalars().all()
            for wf in wfs:
                await SearchIndexer.index_entity(
                    db=db,
                    entity_type="workflow",
                    entity_id=wf.id,
                    title=getattr(wf, 'name', 'Workflow Definition'),
                    content=getattr(wf, 'description', '') or f"Workflow code: {getattr(wf, 'code', '')}",
                    workspace_id=getattr(wf, 'workspace_id', None),
                    organization_id=getattr(wf, 'organization_id', None),
                    owner_id=getattr(wf, 'created_by', None),
                    tags=["workflow", "automation"],
                    metadata_json={"status": "active" if getattr(wf, 'is_active', True) else "inactive"}
                )
                indexed_count += 1
        except Exception as e:
            logger.warning(f"Error seeding workflows into search index: {e}")

        # 7. Workspaces
        try:
            ws_stmt = select(Workspace)
            workspaces = (await db.execute(ws_stmt)).scalars().all()
            for ws in workspaces:
                await SearchIndexer.index_entity(
                    db=db,
                    entity_type="workspace",
                    entity_id=ws.id,
                    title=f"Workspace: {ws.name}",
                    content=ws.description or f"Workspace slug: {ws.slug}",
                    workspace_id=ws.id,
                    organization_id=ws.organization_id,
                    owner_id=ws.created_by,
                    tags=["workspace"],
                    metadata_json={"slug": ws.slug}
                )
                indexed_count += 1
        except Exception as e:
            logger.warning(f"Error seeding workspaces into search index: {e}")

        # 8. Shared Files (Attachments)
        try:
            from ..models.attachments import Attachment
            from ..models.conversations import Conversation
            att_stmt = select(Attachment, Conversation).outerjoin(
                Conversation, Attachment.conversation_id == Conversation.id
            ).where(Attachment.status == "active", Attachment.is_active == True)
            att_res = await db.execute(att_stmt)
            for att, conv in att_res.all():
                conv_name = conv.name if (conv and conv.name) else "Direct Collaboration"
                mime_tag = att.mime_type.split('/')[-1] if att.mime_type else "file"
                await SearchIndexer.index_entity(
                    db=db,
                    entity_type="shared_file",
                    entity_id=att.id,
                    title=att.original_filename,
                    content=f"Shared file: {att.original_filename} in {conv_name}",
                    workspace_id=att.workspace_id,
                    organization_id=att.organization_id,
                    owner_id=att.uploaded_by,
                    tags=["shared_file", mime_tag],
                    metadata_json={
                        "mime_type": att.mime_type,
                        "file_size": att.file_size,
                        "source_title": conv_name,
                        "conversation_id": str(att.conversation_id) if att.conversation_id else None
                    }
                )
                indexed_count += 1
        except Exception as e:
            logger.warning(f"Error seeding shared files into search index: {e}")

        logger.info(f"Auto-seeding search index completed. Processed {indexed_count} items.")
        return indexed_count
