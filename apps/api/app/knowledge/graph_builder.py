import logging
from typing import Dict, Any, Optional
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .graph_service import KnowledgeGraphService
from ..documents.models import Document
from ..models.conversations import Conversation, DirectMessage
from ..models.chat import Chat
from ..projects.models import Project
from ..models.task import Task
from ..models.conversation import ConversationMemory
from ..models.timeline import TimelineEvent, TimelineRelation

logger = logging.getLogger(__name__)

class KnowledgeGraphBuilder:
    """Autonomously constructs nodes and controlled graph edges from existing

    database entities, intelligence summaries, and timeline events without

    making redundant LLM calls.

    """

    def __init__(self, db: AsyncSession):
        self.db = db
        self.service = KnowledgeGraphService(db)

    async def build_graph(self, organization_id: Optional[UUID] = None, limit: int = 100) -> Dict[str, Any]:
        stats = {
            "nodes_created": 0,
            "edges_created": 0
        }

        # 1. Build Project Nodes
        proj_stmt = select(Project).where(Project.deleted_at.is_(None))
        if organization_id:
            proj_stmt = proj_stmt.where(Project.organization_id == organization_id)
        projs = (await self.db.execute(proj_stmt.limit(limit))).scalars().all()

        proj_node_map = {}
        for p in projs:
            p_node = await self.service.get_or_create_node(
                organization_id=p.organization_id,
                workspace_id=p.workspace_id,
                project_id=p.id,
                node_type="PROJECT",
                source_type="project",
                source_id=p.id,
                title=p.name,
                metadata_json={"deep_link": f"/projects/{p.id}"}
            )
            proj_node_map[p.id] = p_node
            stats["nodes_created"] += 1

        # 2. Build Document Nodes & Edges to Projects
        doc_stmt = select(Document).where(Document.deleted_at.is_(None))
        if organization_id:
            doc_stmt = doc_stmt.where(Document.organization_id == organization_id)
        docs = (await self.db.execute(doc_stmt.limit(limit))).scalars().all()

        doc_node_map = {}
        for d in docs:
            d_node = await self.service.get_or_create_node(
                organization_id=d.organization_id,
                workspace_id=d.workspace_id,
                project_id=d.project_id,
                node_type="DOCUMENT",
                source_type="document",
                source_id=d.id,
                title=d.title,
                metadata_json={"filename": d.filename, "mime_type": d.mime_type, "deep_link": f"/files?preview={d.id}"}
            )
            doc_node_map[d.id] = d_node
            stats["nodes_created"] += 1

            if d.project_id and d.project_id in proj_node_map:
                await self.service.create_edge(
                    organization_id=d.organization_id,
                    workspace_id=d.workspace_id,
                    source_node_id=proj_node_map[d.project_id].id,
                    target_node_id=d_node.id,
                    relation_type="CONTAINS",
                    evidence_type="EXPLICIT_FK"
                )
                stats["edges_created"] += 1

        # 3. Build Task Nodes & Edges
        task_stmt = select(Task).where(Task.deleted_at.is_(None))
        if organization_id:
            task_stmt = task_stmt.where(Task.organization_id == organization_id)
        tasks = (await self.db.execute(task_stmt.limit(limit))).scalars().all()

        task_node_map = {}
        for t in tasks:
            t_node = await self.service.get_or_create_node(
                organization_id=t.organization_id,
                project_id=t.project_id,
                node_type="TASK",
                source_type="task",
                source_id=t.id,
                title=f"Task: {t.description[:60]}",
                metadata_json={"status": t.status, "deep_link": f"/tasks/{t.id}"}
            )
            task_node_map[t.id] = t_node
            stats["nodes_created"] += 1

            if t.project_id and t.project_id in proj_node_map:
                await self.service.create_edge(
                    organization_id=t.organization_id,
                    source_node_id=proj_node_map[t.project_id].id,
                    target_node_id=t_node.id,
                    relation_type="CONTAINS",
                    evidence_type="EXPLICIT_FK"
                )
                stats["edges_created"] += 1

        # 4. Build Decision & Memory Nodes & Edges
        mem_stmt = select(ConversationMemory).where(ConversationMemory.deleted_at.is_(None))
        if organization_id:
            mem_stmt = mem_stmt.where(ConversationMemory.organization_id == organization_id)
        mems = (await self.db.execute(mem_stmt.limit(limit))).scalars().all()

        for m in mems:
            n_type = "DECISION" if m.memory_type == "decision" else ("TASK" if m.memory_type == "action_item" else "FACT")
            m_node = await self.service.get_or_create_node(
                organization_id=m.organization_id,
                workspace_id=m.workspace_id,
                project_id=m.project_id,
                node_type=n_type,
                source_type="decision" if m.memory_type == "decision" else "insight",
                source_id=m.id,
                title=m.content[:80],
                metadata_json={
                    "memory_type": m.memory_type,
                    "chat_id": str(m.chat_id) if m.chat_id else None,
                    "conversation_id": str(m.conversation_id) if m.conversation_id else None
                }
            )
            stats["nodes_created"] += 1

            if m.project_id and m.project_id in proj_node_map:
                await self.service.create_edge(
                    organization_id=m.organization_id,
                    workspace_id=m.workspace_id,
                    source_node_id=m_node.id,
                    target_node_id=proj_node_map[m.project_id].id,
                    relation_type="RELATED_TO_PROJECT",
                    evidence_type="AI_DERIVED"
                )
                stats["edges_created"] += 1

        # 5. Build Timeline Event Edges & Lineage
        tl_rel_stmt = select(TimelineRelation).where(TimelineRelation.deleted_at.is_(None))
        tl_rels = (await self.db.execute(tl_rel_stmt.limit(limit))).scalars().all()

        for rel in tl_rels:
            # Fetch source and target timeline events
            ev_src = (await self.db.execute(select(TimelineEvent).where(TimelineEvent.id == rel.source_event_id))).scalar_one_or_none()
            ev_tgt = (await self.db.execute(select(TimelineEvent).where(TimelineEvent.id == rel.target_event_id))).scalar_one_or_none()

            if ev_src and ev_tgt:
                node_src = await self.service.get_or_create_node(
                    organization_id=ev_src.organization_id,
                    workspace_id=ev_src.workspace_id,
                    project_id=ev_src.project_id,
                    node_type="TIMELINE_EVENT",
                    source_type=ev_src.source_type,
                    source_id=ev_src.source_id,
                    title=ev_src.title
                )
                node_tgt = await self.service.get_or_create_node(
                    organization_id=ev_tgt.organization_id,
                    workspace_id=ev_tgt.workspace_id,
                    project_id=ev_tgt.project_id,
                    node_type="TIMELINE_EVENT",
                    source_type=ev_tgt.source_type,
                    source_id=ev_tgt.source_id,
                    title=ev_tgt.title
                )
                await self.service.create_edge(
                    organization_id=ev_src.organization_id,
                    workspace_id=ev_src.workspace_id,
                    source_node_id=node_src.id,
                    target_node_id=node_tgt.id,
                    relation_type=rel.relation_type,
                    evidence_type="TIMELINE_LINEAGE"
                )
                stats["edges_created"] += 1

        await self.db.flush()
        logger.info(f"Knowledge graph build completed: {stats}")
        return stats
