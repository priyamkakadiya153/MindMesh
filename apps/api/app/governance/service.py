import logging
from typing import List, Dict, Any, Optional
from uuid import UUID
from datetime import datetime
from sqlalchemy import select, update, or_, and_, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.models.knowledge_governance import KnowledgeGovernance, GovernanceAuditLog
from app.models.conversation import ConversationMemory
from app.documents.models import Document
from app.models.task import Task

logger = logging.getLogger(__name__)

class GovernanceService:
    """Core service for managing knowledge governance lifecycles (ACTIVE, SUPERSEDED, ARCHIVED),

    human verification states, review queues, supersession relationships, and immutable audit logs.

    """

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_or_create_governance(
        self,
        entity_type: str,
        entity_id: UUID,
        organization_id: UUID,
        workspace_id: Optional[UUID] = None,
        project_id: Optional[UUID] = None
    ) -> KnowledgeGovernance:
        """Retrieves or creates governance metadata for a knowledge entity."""
        stmt = select(KnowledgeGovernance).where(
            KnowledgeGovernance.organization_id == organization_id,
            KnowledgeGovernance.entity_type == entity_type,
            KnowledgeGovernance.entity_id == entity_id
        )
        gov = (await self.db.execute(stmt)).scalar_one_or_none()
        if not gov:
            # Auto-resolve workspace_id if not explicitly provided
            if not workspace_id:
                if entity_type == "DECISION":
                    mem = (await self.db.execute(select(ConversationMemory).where(ConversationMemory.id == entity_id))).scalar_one_or_none()
                    if mem:
                        workspace_id = mem.workspace_id
                        project_id = mem.project_id
                elif entity_type == "DOCUMENT":
                    doc = (await self.db.execute(select(Document).where(Document.id == entity_id))).scalar_one_or_none()
                    if doc:
                        workspace_id = doc.workspace_id
                        project_id = doc.project_id
                elif entity_type == "TASK":
                    tsk = (await self.db.execute(select(Task).where(Task.id == entity_id))).scalar_one_or_none()
                    if tsk:
                        workspace_id = tsk.workspace_id
                        project_id = tsk.project_id

            gov = KnowledgeGovernance(
                organization_id=organization_id,
                workspace_id=workspace_id,
                project_id=project_id,
                entity_type=entity_type,
                entity_id=entity_id,
                lifecycle_state="ACTIVE",
                verification_state="UNVERIFIED",
                authority_state="NORMAL"
            )
            self.db.add(gov)
            await self.db.flush()

        return gov

    async def verify_knowledge(
        self,
        entity_type: str,
        entity_id: UUID,
        user: User,
        organization_id: UUID
    ) -> KnowledgeGovernance:
        """Verifies a knowledge item by human user, recording verified_by and audit log."""
        gov = await self.get_or_create_governance(entity_type, entity_id, organization_id)
        prev_state = gov.verification_state

        gov.verification_state = "VERIFIED"
        gov.verified_by = user.id
        gov.verified_at = datetime.utcnow()
        gov.updated_at = datetime.utcnow()

        audit = GovernanceAuditLog(
            organization_id=organization_id,
            workspace_id=gov.workspace_id,
            user_id=user.id,
            entity_type=entity_type,
            entity_id=entity_id,
            action="VERIFY",
            previous_state=prev_state,
            new_state="VERIFIED",
            details=f"Knowledge verified by {user.first_name or 'User'} {user.last_name or ''}"
        )
        self.db.add(audit)
        await self.db.flush()
        return gov

    async def supersede_knowledge(
        self,
        old_entity_type: str,
        old_entity_id: UUID,
        new_entity_id: UUID,
        user: User,
        organization_id: UUID
    ) -> KnowledgeGovernance:
        """Marks old knowledge item SUPERSEDED by a newer knowledge item."""
        old_gov = await self.get_or_create_governance(old_entity_type, old_entity_id, organization_id)
        prev_state = old_gov.lifecycle_state

        old_gov.lifecycle_state = "SUPERSEDED"
        old_gov.superseded_by = new_entity_id
        old_gov.updated_at = datetime.utcnow()

        audit = GovernanceAuditLog(
            organization_id=organization_id,
            workspace_id=old_gov.workspace_id,
            user_id=user.id,
            entity_type=old_entity_type,
            entity_id=old_entity_id,
            action="SUPERSEDE",
            previous_state=prev_state,
            new_state="SUPERSEDED",
            details=f"Superseded by new entity {new_entity_id}"
        )
        self.db.add(audit)
        await self.db.flush()
        return old_gov

    async def archive_knowledge(
        self,
        entity_type: str,
        entity_id: UUID,
        user: User,
        organization_id: UUID
    ) -> KnowledgeGovernance:
        """Archives a knowledge item."""
        gov = await self.get_or_create_governance(entity_type, entity_id, organization_id)
        prev_state = gov.lifecycle_state

        gov.lifecycle_state = "ARCHIVED"
        gov.archived_at = datetime.utcnow()
        gov.updated_at = datetime.utcnow()

        audit = GovernanceAuditLog(
            organization_id=organization_id,
            workspace_id=gov.workspace_id,
            user_id=user.id,
            entity_type=entity_type,
            entity_id=entity_id,
            action="ARCHIVE",
            previous_state=prev_state,
            new_state="ARCHIVED",
            details="Knowledge archived by user"
        )
        self.db.add(audit)
        await self.db.flush()
        return gov

    async def restore_knowledge(
        self,
        entity_type: str,
        entity_id: UUID,
        user: User,
        organization_id: UUID
    ) -> KnowledgeGovernance:
        """Restores an archived knowledge item to ACTIVE."""
        gov = await self.get_or_create_governance(entity_type, entity_id, organization_id)
        prev_state = gov.lifecycle_state

        gov.lifecycle_state = "ACTIVE"
        gov.archived_at = None
        gov.updated_at = datetime.utcnow()

        audit = GovernanceAuditLog(
            organization_id=organization_id,
            workspace_id=gov.workspace_id,
            user_id=user.id,
            entity_type=entity_type,
            entity_id=entity_id,
            action="RESTORE",
            previous_state=prev_state,
            new_state="ACTIVE",
            details="Knowledge restored to active state"
        )
        self.db.add(audit)
        await self.db.flush()
        return gov

    async def get_review_queue(
        self,
        organization_id: UUID,
        workspace_id: Optional[UUID] = None,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """Surfaces items requiring review (unverified decisions, conflicts, source drift)."""
        review_items: List[Dict[str, Any]] = []

        # 1. Unverified Decisions
        d_stmt = select(ConversationMemory).where(
            ConversationMemory.organization_id == organization_id,
            ConversationMemory.memory_type == "decision",
            ConversationMemory.deleted_at.is_(None)
        ).order_by(desc(ConversationMemory.created_at)).limit(limit)

        if workspace_id:
            d_stmt = d_stmt.where(ConversationMemory.workspace_id == workspace_id)

        decisions = (await self.db.execute(d_stmt)).scalars().all()

        for d in decisions:
            gov = await self.get_or_create_governance("DECISION", d.id, organization_id, d.workspace_id, d.project_id)
            if gov.verification_state != "VERIFIED" and gov.lifecycle_state == "ACTIVE":
                review_items.append({
                    "id": str(d.id),
                    "entity_type": "DECISION",
                    "entity_id": str(d.id),
                    "title": "Unverified Decision",
                    "summary": d.content,
                    "reason": "AI-extracted decision has not been manually verified by a team member.",
                    "priority": "HIGH" if gov.review_reason else "NORMAL",
                    "verification_state": gov.verification_state,
                    "lifecycle_state": gov.lifecycle_state
                })

        return review_items[:limit]

    async def get_audit_trail(
        self,
        organization_id: UUID,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """Retrieves immutable governance audit records."""
        stmt = select(GovernanceAuditLog).where(
            GovernanceAuditLog.organization_id == organization_id
        ).order_by(desc(GovernanceAuditLog.created_at)).limit(limit)

        logs = (await self.db.execute(stmt)).scalars().all()
        return [
            {
                "id": str(l.id),
                "action": l.action,
                "entity_type": l.entity_type,
                "entity_id": str(l.entity_id),
                "previous_state": l.previous_state,
                "new_state": l.new_state,
                "user_id": str(l.user_id),
                "details": l.details,
                "created_at": l.created_at.isoformat() if l.created_at else ""
            }
            for l in logs
        ]
