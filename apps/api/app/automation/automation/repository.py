import logging
from uuid import UUID
from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.automation.approval.models import WorkflowDefinition, WorkflowExecution

logger = logging.getLogger(__name__)

class AutomationRepository:
    @staticmethod
    async def create_workflow(db: AsyncSession, wdef: WorkflowDefinition) -> WorkflowDefinition:
        db.add(wdef)
        await db.flush()
        return wdef

    @staticmethod
    async def get_workflow(db: AsyncSession, workflow_id: UUID) -> Optional[WorkflowDefinition]:
        stmt = select(WorkflowDefinition).where(WorkflowDefinition.id == workflow_id)
        res = await db.execute(stmt)
        return res.scalar_one_or_none()

    @staticmethod
    async def list_workflows(db: AsyncSession, organization_id: UUID) -> List[WorkflowDefinition]:
        stmt = select(WorkflowDefinition).where(WorkflowDefinition.organization_id == organization_id)
        res = await db.execute(stmt)
        return list(res.scalars().all())

    @staticmethod
    async def get_execution(db: AsyncSession, execution_id: UUID) -> Optional[WorkflowExecution]:
        stmt = select(WorkflowExecution).where(WorkflowExecution.id == execution_id)
        res = await db.execute(stmt)
        return res.scalar_one_or_none()

    @staticmethod
    async def list_executions(db: AsyncSession, organization_id: UUID) -> List[WorkflowExecution]:
        stmt = select(WorkflowExecution).where(WorkflowExecution.organization_id == organization_id)
        res = await db.execute(stmt)
        return list(res.scalars().all())
