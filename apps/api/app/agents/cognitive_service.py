"""
MindMesh — Cognitive Agent Business Service Layer (CA-02)

Enforces RBAC authorization, user-organization-workspace membership validation,
and input validation for Cognitive Agent operations.
"""

from typing import List, Optional, Dict, Any
from uuid import UUID
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.user import User
from app.models.organization import Organization
from app.workspace.models import Workspace
from app.models.cognitive_agent import (
    CognitiveAgent,
    CognitiveAgentExecution,
    CognitiveAgentOutput
)
from app.agents.cognitive_repository import CognitiveAgentRepository
from app.agents.cognitive_schemas import (
    CognitiveAgentCreate,
    CognitiveAgentUpdate
)


class CognitiveAgentService:

    @staticmethod
    async def _validate_workspace_access(
        db: AsyncSession,
        organization_id: UUID,
        workspace_id: Optional[UUID]
    ):
        if workspace_id:
            stmt = select(Workspace).where(
                Workspace.id == workspace_id,
                Workspace.organization_id == organization_id,
                Workspace.deleted_at.is_(None)
            )
            res = await db.execute(stmt)
            ws = res.scalar_one_or_none()
            if not ws:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Workspace '{workspace_id}' not found in organization."
                )

    @staticmethod
    async def create_agent(
        db: AsyncSession,
        current_user: User,
        organization_id: UUID,
        payload: CognitiveAgentCreate
    ) -> CognitiveAgent:
        # Validate Organization existence
        stmt_org = select(Organization).where(Organization.id == organization_id, Organization.deleted_at.is_(None))
        res_org = await db.execute(stmt_org)
        if not res_org.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Organization '{organization_id}' not found."
            )

        await CognitiveAgentService._validate_workspace_access(
            db, organization_id, payload.workspace_id
        )

        scope_dict = payload.knowledge_scope.model_dump() if payload.knowledge_scope else None
        triggers_list = [t.model_dump() for t in payload.triggers] if payload.triggers else None

        return await CognitiveAgentRepository.create_agent(
            db=db,
            organization_id=organization_id,
            owner_user_id=current_user.id,
            name=payload.name,
            instructions=payload.instructions,
            description=payload.description,
            workspace_id=payload.workspace_id,
            agent_type=payload.agent_type.value if hasattr(payload.agent_type, 'value') else payload.agent_type,
            status="ACTIVE",
            enabled=payload.enabled,
            knowledge_scope=scope_dict,
            triggers=triggers_list
        )

    @staticmethod
    async def get_agent(
        db: AsyncSession,
        agent_id: UUID,
        organization_id: UUID,
        workspace_id: Optional[UUID] = None
    ) -> CognitiveAgent:
        agent = await CognitiveAgentRepository.get_agent_by_id(
            db=db,
            agent_id=agent_id,
            organization_id=organization_id,
            workspace_id=workspace_id
        )
        if not agent:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Cognitive Agent '{agent_id}' not found or access denied."
            )
        return agent

    @staticmethod
    async def list_agents(
        db: AsyncSession,
        organization_id: UUID,
        workspace_id: Optional[UUID] = None
    ) -> List[CognitiveAgent]:
        return await CognitiveAgentRepository.list_agents(
            db=db,
            organization_id=organization_id,
            workspace_id=workspace_id
        )

    @staticmethod
    async def update_agent(
        db: AsyncSession,
        current_user: User,
        agent_id: UUID,
        organization_id: UUID,
        payload: CognitiveAgentUpdate
    ) -> CognitiveAgent:
        # Verify agent exists & belongs to org
        agent = await CognitiveAgentService.get_agent(db, agent_id, organization_id)

        updates: Dict[str, Any] = {}
        if payload.name is not None:
            updates["name"] = payload.name
        if payload.description is not None:
            updates["description"] = payload.description
        if payload.instructions is not None:
            updates["instructions"] = payload.instructions
        if payload.status is not None:
            updates["status"] = payload.status.value if hasattr(payload.status, 'value') else payload.status
        if payload.enabled is not None:
            updates["enabled"] = payload.enabled
        if payload.knowledge_scope is not None:
            updates["knowledge_scope"] = payload.knowledge_scope.model_dump()
        if payload.triggers is not None:
            updates["triggers"] = [t.model_dump() for t in payload.triggers]

        updated_agent = await CognitiveAgentRepository.update_agent(
            db=db,
            agent_id=agent_id,
            organization_id=organization_id,
            updates=updates
        )
        if not updated_agent:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to update agent.")
        return updated_agent

    @staticmethod
    async def archive_agent(
        db: AsyncSession,
        current_user: User,
        agent_id: UUID,
        organization_id: UUID
    ) -> bool:
        await CognitiveAgentService.get_agent(db, agent_id, organization_id)
        return await CognitiveAgentRepository.archive_agent(db, agent_id, organization_id)

    # ---------------- EXECUTIONS ----------------

    @staticmethod
    async def record_execution(
        db: AsyncSession,
        agent_id: UUID,
        organization_id: UUID,
        triggered_by: Optional[UUID] = None,
        trigger_type: str = "MANUAL",
        input_context: Optional[Dict[str, Any]] = None
    ) -> CognitiveAgentExecution:
        agent = await CognitiveAgentService.get_agent(db, agent_id, organization_id)
        return await CognitiveAgentRepository.create_execution(
            db=db,
            agent_id=agent.id,
            organization_id=organization_id,
            workspace_id=agent.workspace_id,
            triggered_by=triggered_by,
            trigger_type=trigger_type,
            input_context=input_context,
            status="QUEUED"
        )

    @staticmethod
    async def list_agent_executions(
        db: AsyncSession,
        agent_id: UUID,
        organization_id: UUID
    ) -> List[CognitiveAgentExecution]:
        await CognitiveAgentService.get_agent(db, agent_id, organization_id)
        return await CognitiveAgentRepository.list_agent_executions(db, agent_id, organization_id)

    # ---------------- OUTPUTS & PROVENANCE ----------------

    @staticmethod
    async def list_agent_outputs(
        db: AsyncSession,
        current_user: User,
        agent_id: UUID,
        organization_id: UUID
    ) -> List[CognitiveAgentOutput]:
        agent = await CognitiveAgentService.get_agent(db, agent_id, organization_id)
        outputs = await CognitiveAgentRepository.list_agent_outputs(
            db=db,
            agent_id=agent_id,
            organization_id=organization_id,
            workspace_id=agent.workspace_id
        )

        from app.agents.cognitive_provenance import CognitiveAgentProvenanceService
        for out in outputs:
            out.provenance = await CognitiveAgentProvenanceService.revalidate_output_provenance(
                db=db,
                current_user=current_user,
                organization_id=organization_id,
                workspace_id=out.workspace_id or agent.workspace_id,
                raw_provenance=out.provenance,
                output_created_at=out.created_at
            )
        return outputs

    @staticmethod
    async def get_agent_output_detail(
        db: AsyncSession,
        current_user: User,
        agent_id: UUID,
        output_id: UUID,
        organization_id: UUID
    ) -> CognitiveAgentOutput:
        agent = await CognitiveAgentService.get_agent(db, agent_id, organization_id)
        output = await CognitiveAgentRepository.get_output_by_id(db, output_id, organization_id)
        if not output or output.agent_id != agent.id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cognitive Agent Output not found.")

        from app.agents.cognitive_provenance import CognitiveAgentProvenanceService
        output.provenance = await CognitiveAgentProvenanceService.revalidate_output_provenance(
            db=db,
            current_user=current_user,
            organization_id=organization_id,
            workspace_id=output.workspace_id or agent.workspace_id,
            raw_provenance=output.provenance,
            output_created_at=output.created_at
        )
        return output

    @staticmethod
    async def get_execution_output(
        db: AsyncSession,
        current_user: User,
        agent_id: UUID,
        execution_id: UUID,
        organization_id: UUID
    ) -> Optional[CognitiveAgentOutput]:
        agent = await CognitiveAgentService.get_agent(db, agent_id, organization_id)
        output = await CognitiveAgentRepository.get_execution_output(db, execution_id, organization_id)
        if not output or output.agent_id != agent.id:
            return None

        from app.agents.cognitive_provenance import CognitiveAgentProvenanceService
        output.provenance = await CognitiveAgentProvenanceService.revalidate_output_provenance(
            db=db,
            current_user=current_user,
            organization_id=organization_id,
            workspace_id=output.workspace_id or agent.workspace_id,
            raw_provenance=output.provenance,
            output_created_at=output.created_at
        )
        return output

