"""
MindMesh — Cognitive Agent Database Repository Layer (CA-02)

Provides PostgreSQL database CRUD operations with strict organization and workspace isolation filtering.
"""

from typing import List, Optional, Dict, Any
from uuid import UUID
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, and_, or_

from app.models.cognitive_agent import (
    CognitiveAgent,
    CognitiveAgentExecution,
    CognitiveAgentOutput
)


class CognitiveAgentRepository:

    @staticmethod
    async def create_agent(
        db: AsyncSession,
        organization_id: UUID,
        owner_user_id: UUID,
        name: str,
        instructions: str,
        description: Optional[str] = None,
        workspace_id: Optional[UUID] = None,
        agent_type: str = "CUSTOM",
        status: str = "ACTIVE",
        enabled: bool = True,
        knowledge_scope: Optional[Dict[str, Any]] = None,
        triggers: Optional[List[Dict[str, Any]]] = None
    ) -> CognitiveAgent:
        agent = CognitiveAgent(
            organization_id=organization_id,
            workspace_id=workspace_id,
            owner_user_id=owner_user_id,
            name=name,
            description=description,
            agent_type=agent_type,
            instructions=instructions,
            status=status,
            enabled=enabled,
            knowledge_scope=knowledge_scope,
            triggers=triggers,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        db.add(agent)
        await db.commit()
        await db.refresh(agent)
        return agent

    @staticmethod
    async def get_agent_by_id(
        db: AsyncSession,
        agent_id: UUID,
        organization_id: UUID,
        workspace_id: Optional[UUID] = None
    ) -> Optional[CognitiveAgent]:
        conditions = [
            CognitiveAgent.id == agent_id,
            CognitiveAgent.organization_id == organization_id,
            CognitiveAgent.deleted_at.is_(None)
        ]
        if workspace_id:
            conditions.append(CognitiveAgent.workspace_id == workspace_id)

        stmt = select(CognitiveAgent).where(and_(*conditions))
        res = await db.execute(stmt)
        return res.scalar_one_or_none()

    @staticmethod
    async def list_agents(
        db: AsyncSession,
        organization_id: UUID,
        workspace_id: Optional[UUID] = None,
        include_archived: bool = False
    ) -> List[CognitiveAgent]:
        conditions = [
            CognitiveAgent.organization_id == organization_id,
            CognitiveAgent.deleted_at.is_(None)
        ]
        if workspace_id:
            conditions.append(
                or_(
                    CognitiveAgent.workspace_id == workspace_id,
                    CognitiveAgent.workspace_id.is_(None)
                )
            )
        if not include_archived:
            conditions.append(CognitiveAgent.status != "ARCHIVED")

        stmt = select(CognitiveAgent).where(and_(*conditions)).order_by(CognitiveAgent.created_at.desc())
        res = await db.execute(stmt)
        return list(res.scalars().all())

    @staticmethod
    async def update_agent(
        db: AsyncSession,
        agent_id: UUID,
        organization_id: UUID,
        updates: Dict[str, Any]
    ) -> Optional[CognitiveAgent]:
        updates["updated_at"] = datetime.utcnow()
        stmt = (
            update(CognitiveAgent)
            .where(
                and_(
                    CognitiveAgent.id == agent_id,
                    CognitiveAgent.organization_id == organization_id,
                    CognitiveAgent.deleted_at.is_(None)
                )
            )
            .values(**updates)
            .execution_options(synchronize_session="fetch")
        )
        await db.execute(stmt)
        await db.commit()
        return await CognitiveAgentRepository.get_agent_by_id(db, agent_id, organization_id)

    @staticmethod
    async def archive_agent(
        db: AsyncSession,
        agent_id: UUID,
        organization_id: UUID
    ) -> bool:
        """Soft deletes / archives an agent preserving referential audit history."""
        now = datetime.utcnow()
        stmt = (
            update(CognitiveAgent)
            .where(
                and_(
                    CognitiveAgent.id == agent_id,
                    CognitiveAgent.organization_id == organization_id,
                    CognitiveAgent.deleted_at.is_(None)
                )
            )
            .values(status="ARCHIVED", enabled=False, deleted_at=now, updated_at=now)
        )
        res = await db.execute(stmt)
        await db.commit()
        return res.rowcount > 0

    # ---------------- EXECUTION PERSISTENCE ----------------

    @staticmethod
    async def create_execution(
        db: AsyncSession,
        agent_id: UUID,
        organization_id: UUID,
        workspace_id: Optional[UUID] = None,
        triggered_by: Optional[UUID] = None,
        trigger_type: str = "MANUAL",
        input_context: Optional[Dict[str, Any]] = None,
        status: str = "QUEUED"
    ) -> CognitiveAgentExecution:
        execution = CognitiveAgentExecution(
            agent_id=agent_id,
            organization_id=organization_id,
            workspace_id=workspace_id,
            triggered_by=triggered_by,
            trigger_type=trigger_type,
            status=status,
            input_context=input_context,
            started_at=datetime.utcnow(),
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        db.add(execution)
        await db.commit()
        await db.refresh(execution)
        return execution

    @staticmethod
    async def update_execution_status(
        db: AsyncSession,
        execution_id: UUID,
        organization_id: UUID,
        status: str,
        output_summary: Optional[str] = None,
        action_candidates_generated: int = 0,
        error_message: Optional[str] = None
    ) -> Optional[CognitiveAgentExecution]:
        values: Dict[str, Any] = {
            "status": status,
            "updated_at": datetime.utcnow()
        }
        if status in ("COMPLETED", "FAILED", "CANCELLED"):
            values["completed_at"] = datetime.utcnow()
        if output_summary is not None:
            values["output_summary"] = output_summary
        if action_candidates_generated:
            values["action_candidates_generated"] = action_candidates_generated
        if error_message is not None:
            values["error_message"] = error_message

        stmt = (
            update(CognitiveAgentExecution)
            .where(
                and_(
                    CognitiveAgentExecution.id == execution_id,
                    CognitiveAgentExecution.organization_id == organization_id
                )
            )
            .values(**values)
        )
        await db.execute(stmt)
        await db.commit()

        stmt_get = select(CognitiveAgentExecution).where(
            and_(
                CognitiveAgentExecution.id == execution_id,
                CognitiveAgentExecution.organization_id == organization_id
            )
        )
        res = await db.execute(stmt_get)
        return res.scalar_one_or_none()

    @staticmethod
    async def list_agent_executions(
        db: AsyncSession,
        agent_id: UUID,
        organization_id: UUID
    ) -> List[CognitiveAgentExecution]:
        stmt = (
            select(CognitiveAgentExecution)
            .where(
                and_(
                    CognitiveAgentExecution.agent_id == agent_id,
                    CognitiveAgentExecution.organization_id == organization_id
                )
            )
            .order_by(CognitiveAgentExecution.created_at.desc())
        )
        res = await db.execute(stmt)
        return list(res.scalars().all())

    # ---------------- OUTPUT PERSISTENCE ----------------

    @staticmethod
    async def create_output(
        db: AsyncSession,
        execution_id: UUID,
        agent_id: UUID,
        organization_id: UUID,
        title: str,
        body: str,
        output_type: str = "INSIGHT",
        workspace_id: Optional[UUID] = None,
        candidate_type: Optional[str] = None,
        structured_payload: Optional[Dict[str, Any]] = None,
        provenance: Optional[List[Dict[str, Any]]] = None
    ) -> CognitiveAgentOutput:
        output = CognitiveAgentOutput(
            execution_id=execution_id,
            agent_id=agent_id,
            organization_id=organization_id,
            workspace_id=workspace_id,
            output_type=output_type,
            title=title,
            body=body,
            candidate_type=candidate_type,
            structured_payload=structured_payload,
            provenance=provenance,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        db.add(output)
        await db.commit()
        await db.refresh(output)
        return output

    @staticmethod
    async def list_agent_outputs(
        db: AsyncSession,
        agent_id: UUID,
        organization_id: UUID,
        workspace_id: Optional[UUID] = None
    ) -> List[CognitiveAgentOutput]:
        conditions = [
            CognitiveAgentOutput.agent_id == agent_id,
            CognitiveAgentOutput.organization_id == organization_id,
            CognitiveAgentOutput.deleted_at.is_(None)
        ]
        if workspace_id:
            conditions.append(CognitiveAgentOutput.workspace_id == workspace_id)

        stmt = select(CognitiveAgentOutput).where(and_(*conditions)).order_by(CognitiveAgentOutput.created_at.desc())
        res = await db.execute(stmt)
        return list(res.scalars().all())

    @staticmethod
    async def get_output_by_id(
        db: AsyncSession,
        output_id: UUID,
        organization_id: UUID
    ) -> Optional[CognitiveAgentOutput]:
        stmt = select(CognitiveAgentOutput).where(
            and_(
                CognitiveAgentOutput.id == output_id,
                CognitiveAgentOutput.organization_id == organization_id,
                CognitiveAgentOutput.deleted_at.is_(None)
            )
        )
        res = await db.execute(stmt)
        return res.scalar_one_or_none()

    @staticmethod
    async def get_execution_output(
        db: AsyncSession,
        execution_id: UUID,
        organization_id: UUID
    ) -> Optional[CognitiveAgentOutput]:
        stmt = select(CognitiveAgentOutput).where(
            and_(
                CognitiveAgentOutput.execution_id == execution_id,
                CognitiveAgentOutput.organization_id == organization_id,
                CognitiveAgentOutput.deleted_at.is_(None)
            )
        )
        res = await db.execute(stmt)
        return res.scalar_one_or_none()

