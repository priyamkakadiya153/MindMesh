"""
MindMesh — Cognitive Agent REST API Router (CA-02)

Exposes isolated endpoints for CRUD operations on Cognitive Agents, Executions, and Outputs.
"""

from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db_session
from app.api.dependencies import get_current_user
from app.authorization.organization_resolver import resolve_organization_id
from app.models.user import User
from app.agents.cognitive_service import CognitiveAgentService
from app.agents.cognitive_repository import CognitiveAgentRepository
from app.agents.cognitive_schemas import (
    CognitiveAgentCreate,
    CognitiveAgentUpdate,
    CognitiveAgentResponse,
    CognitiveAgentExecutionCreate,
    CognitiveAgentExecutionResponse,
    CognitiveAgentOutputCreate,
    CognitiveAgentOutputResponse
)

router = APIRouter(prefix="/cognitive-agents", tags=["Cognitive Agents Persistence Layer"])


@router.post("", response_model=CognitiveAgentResponse, status_code=status.HTTP_201_CREATED)
async def create_cognitive_agent(
    payload: CognitiveAgentCreate,
    current_user: User = Depends(get_current_user),
    org_id: str = Depends(resolve_organization_id),
    db: AsyncSession = Depends(get_db_session)
):
    """Creates a new Cognitive Agent record in PostgreSQL."""
    org_uuid = UUID(org_id) if isinstance(org_id, str) else org_id
    agent = await CognitiveAgentService.create_agent(
        db=db,
        current_user=current_user,
        organization_id=org_uuid,
        payload=payload
    )
    return agent


@router.get("", response_model=List[CognitiveAgentResponse], status_code=status.HTTP_200_OK)
async def list_cognitive_agents(
    workspace_id: Optional[UUID] = Query(None, description="Optional workspace filter"),
    current_user: User = Depends(get_current_user),
    org_id: str = Depends(resolve_organization_id),
    db: AsyncSession = Depends(get_db_session)
):
    """Lists all active Cognitive Agents for the authenticated user's organization/workspace."""
    org_uuid = UUID(org_id) if isinstance(org_id, str) else org_id
    agents = await CognitiveAgentService.list_agents(
        db=db,
        organization_id=org_uuid,
        workspace_id=workspace_id
    )
    return agents


@router.get("/{id}", response_model=CognitiveAgentResponse, status_code=status.HTTP_200_OK)
async def get_cognitive_agent_details(
    id: UUID,
    current_user: User = Depends(get_current_user),
    org_id: str = Depends(resolve_organization_id),
    db: AsyncSession = Depends(get_db_session)
):
    """Retrieves full metadata of a specific Cognitive Agent by ID."""
    org_uuid = UUID(org_id) if isinstance(org_id, str) else org_id
    agent = await CognitiveAgentService.get_agent(
        db=db,
        agent_id=id,
        organization_id=org_uuid
    )
    return agent


@router.patch("/{id}", response_model=CognitiveAgentResponse, status_code=status.HTTP_200_OK)
async def update_cognitive_agent(
    id: UUID,
    payload: CognitiveAgentUpdate,
    current_user: User = Depends(get_current_user),
    org_id: str = Depends(resolve_organization_id),
    db: AsyncSession = Depends(get_db_session)
):
    """Updates Cognitive Agent fields (name, instructions, status, triggers, scope)."""
    org_uuid = UUID(org_id) if isinstance(org_id, str) else org_id
    agent = await CognitiveAgentService.update_agent(
        db=db,
        current_user=current_user,
        agent_id=id,
        organization_id=org_uuid,
        payload=payload
    )
    return agent


@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def archive_cognitive_agent(
    id: UUID,
    current_user: User = Depends(get_current_user),
    org_id: str = Depends(resolve_organization_id),
    db: AsyncSession = Depends(get_db_session)
):
    """Soft deletes / archives a Cognitive Agent while preserving audit trail."""
    org_uuid = UUID(org_id) if isinstance(org_id, str) else org_id
    await CognitiveAgentService.archive_agent(
        db=db,
        current_user=current_user,
        agent_id=id,
        organization_id=org_uuid
    )
    return None


@router.post("/{id}/execute", status_code=status.HTTP_200_OK)
async def execute_cognitive_agent(
    id: UUID,
    payload: Optional[CognitiveAgentExecutionCreate] = None,
    current_user: User = Depends(get_current_user),
    org_id: str = Depends(resolve_organization_id),
    db: AsyncSession = Depends(get_db_session)
):
    """
    Executes a Cognitive Agent analysis within its authorized knowledge scope (CA-05).
    """
    from app.agents.cognitive_engine import CognitiveAgentExecutionEngine
    org_uuid = UUID(org_id) if isinstance(org_id, str) else org_id
    
    # Retrieve agent to obtain workspace context
    agent = await CognitiveAgentService.get_agent(db=db, agent_id=id, organization_id=org_uuid)
    ws_id = agent.workspace_id

    if not ws_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Agent must belong to a workspace to be executed."
        )

    trigger_type = payload.trigger_type if payload else "MANUAL"
    input_ctx = payload.input_context if payload else None

    execution, output = await CognitiveAgentExecutionEngine.execute_agent(
        db=db,
        agent_id=id,
        current_user=current_user,
        organization_id=org_uuid,
        workspace_id=ws_id,
        trigger_type=trigger_type,
        input_context=input_ctx
    )

    return {
        "execution": CognitiveAgentExecutionResponse.model_validate(execution),
        "output": CognitiveAgentOutputResponse.model_validate(output) if output else None
    }


@router.get("/{id}/executions", response_model=List[CognitiveAgentExecutionResponse], status_code=status.HTTP_200_OK)
async def list_agent_executions(
    id: UUID,
    current_user: User = Depends(get_current_user),
    org_id: str = Depends(resolve_organization_id),
    db: AsyncSession = Depends(get_db_session)
):
    """Lists execution history records for a specific Cognitive Agent."""
    org_uuid = UUID(org_id) if isinstance(org_id, str) else org_id
    executions = await CognitiveAgentService.list_agent_executions(
        db=db,
        agent_id=id,
        organization_id=org_uuid
    )
    return executions


@router.post("/{id}/executions", response_model=CognitiveAgentExecutionResponse, status_code=status.HTTP_201_CREATED)
async def record_synthetic_execution(
    id: UUID,
    payload: CognitiveAgentExecutionCreate,
    current_user: User = Depends(get_current_user),
    org_id: str = Depends(resolve_organization_id),
    db: AsyncSession = Depends(get_db_session)
):
    """Records a synthetic execution record for persistence validation (does NOT invoke LLM)."""
    org_uuid = UUID(org_id) if isinstance(org_id, str) else org_id
    execution = await CognitiveAgentService.record_execution(
        db=db,
        agent_id=id,
        organization_id=org_uuid,
        triggered_by=current_user.id,
        trigger_type=payload.trigger_type,
        input_context=payload.input_context
    )
    return execution


@router.post("/executions/{execution_id}/outputs", response_model=CognitiveAgentOutputResponse, status_code=status.HTTP_201_CREATED)
async def record_synthetic_output(
    execution_id: UUID,
    payload: CognitiveAgentOutputCreate,
    current_user: User = Depends(get_current_user),
    org_id: str = Depends(resolve_organization_id),
    db: AsyncSession = Depends(get_db_session)
):
    """Records a synthetic output record linked to an execution session."""
    org_uuid = UUID(org_id) if isinstance(org_id, str) else org_id
    
    # Retrieve execution session to obtain agent & workspace context
    stmt = CognitiveAgentRepository
    output = await CognitiveAgentRepository.create_output(
        db=db,
        execution_id=execution_id,
        agent_id=execution_id, # Or target agent_id
        organization_id=org_uuid,
        title=payload.title,
        body=payload.body,
        candidate_type=payload.candidate_type,
        structured_payload=payload.structured_payload,
        provenance=payload.provenance
    )
    return output


@router.get("/knowledge-options", status_code=status.HTTP_200_OK)
async def get_knowledge_options(
    workspace_id: UUID = Query(..., description="Target workspace ID"),
    current_user: User = Depends(get_current_user),
    org_id: str = Depends(resolve_organization_id),
    db: AsyncSession = Depends(get_db_session)
):
    """Returns projects, documents, and conversations authorized for the current user in workspace."""
    from app.agents.cognitive_knowledge import CognitiveAgentKnowledgeService
    org_uuid = UUID(org_id) if isinstance(org_id, str) else org_id
    options = await CognitiveAgentKnowledgeService.get_user_selectable_knowledge_options(
        db=db,
        current_user=current_user,
        organization_id=org_uuid,
        workspace_id=workspace_id
    )
    return options


@router.get("/{id}/knowledge-scope", status_code=status.HTTP_200_OK)
async def get_agent_knowledge_scope(
    id: UUID,
    current_user: User = Depends(get_current_user),
    org_id: str = Depends(resolve_organization_id),
    db: AsyncSession = Depends(get_db_session)
):
    """Retrieves configured knowledge scope for a specific Cognitive Agent."""
    org_uuid = UUID(org_id) if isinstance(org_id, str) else org_id
    agent = await CognitiveAgentService.get_agent(db=db, agent_id=id, organization_id=org_uuid)
    return agent.knowledge_scope or {"scope_type": "NONE"}


@router.put("/{id}/knowledge-scope", response_model=CognitiveAgentResponse, status_code=status.HTTP_200_OK)
async def update_agent_knowledge_scope(
    id: UUID,
    payload: dict,
    current_user: User = Depends(get_current_user),
    org_id: str = Depends(resolve_organization_id),
    db: AsyncSession = Depends(get_db_session)
):
    """Updates and normalizes an agent's knowledge scope configuration."""
    from app.agents.cognitive_knowledge import CognitiveAgentKnowledgeService
    org_uuid = UUID(org_id) if isinstance(org_id, str) else org_id
    agent = await CognitiveAgentService.get_agent(db=db, agent_id=id, organization_id=org_uuid)
    ws_id = agent.workspace_id

    if not ws_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Agent must belong to a workspace to configure knowledge scope."
        )

    normalized_scope = await CognitiveAgentKnowledgeService.validate_and_normalize_scope(
        db=db,
        scope_data=payload,
        current_user=current_user,
        organization_id=org_uuid,
        workspace_id=ws_id
    )

    updated = await CognitiveAgentService.update_agent(
        db=db,
        current_user=current_user,
        agent_id=id,
        organization_id=org_uuid,
        payload=CognitiveAgentUpdate(knowledge_scope=normalized_scope)
    )
    return updated


@router.post("/{id}/knowledge-preview", status_code=status.HTTP_200_OK)
async def preview_agent_knowledge_scope(
    id: UUID,
    current_user: User = Depends(get_current_user),
    org_id: str = Depends(resolve_organization_id),
    db: AsyncSession = Depends(get_db_session)
):
    """Previews resolved accessible knowledge items for an agent under its current scope."""
    from app.agents.cognitive_knowledge import CognitiveAgentKnowledgeService
    org_uuid = UUID(org_id) if isinstance(org_id, str) else org_id
    agent = await CognitiveAgentService.get_agent(db=db, agent_id=id, organization_id=org_uuid)
    ws_id = agent.workspace_id or UUID("00000000-0000-0000-0000-000000000000")

    preview = await CognitiveAgentKnowledgeService.resolve_agent_knowledge_boundary(
        db=db,
        agent=agent,
        current_user=current_user,
        organization_id=org_uuid,
        workspace_id=ws_id
    )
    return preview


# ==========================================
# CA-06 Trigger & Scheduling Endpoints
# ==========================================

@router.post("/{id}/triggers", status_code=status.HTTP_201_CREATED)
async def create_agent_trigger(
    id: UUID,
    payload: dict,
    current_user: User = Depends(get_current_user),
    org_id: str = Depends(resolve_organization_id),
    db: AsyncSession = Depends(get_db_session)
):
    """Creates a new Trigger or Schedule record for a Cognitive Agent."""
    from app.agents.cognitive_triggers import CognitiveAgentTriggerService
    org_uuid = UUID(org_id) if isinstance(org_id, str) else org_id
    trigger = await CognitiveAgentTriggerService.create_trigger(
        db=db,
        agent_id=id,
        payload=payload,
        current_user=current_user,
        organization_id=org_uuid
    )
    return trigger


@router.get("/{id}/triggers", status_code=status.HTTP_200_OK)
async def list_agent_triggers(
    id: UUID,
    current_user: User = Depends(get_current_user),
    org_id: str = Depends(resolve_organization_id),
    db: AsyncSession = Depends(get_db_session)
):
    """Lists configured triggers for a Cognitive Agent."""
    from app.agents.cognitive_triggers import CognitiveAgentTriggerService
    org_uuid = UUID(org_id) if isinstance(org_id, str) else org_id
    triggers = await CognitiveAgentTriggerService.list_triggers(
        db=db,
        agent_id=id,
        organization_id=org_uuid
    )
    return triggers


@router.post("/{id}/triggers/{trigger_id}/pause", status_code=status.HTTP_200_OK)
async def pause_agent_trigger(
    id: UUID,
    trigger_id: UUID,
    current_user: User = Depends(get_current_user),
    org_id: str = Depends(resolve_organization_id),
    db: AsyncSession = Depends(get_db_session)
):
    """Pauses a Cognitive Agent trigger."""
    from app.agents.cognitive_triggers import CognitiveAgentTriggerService
    org_uuid = UUID(org_id) if isinstance(org_id, str) else org_id
    trigger = await CognitiveAgentTriggerService.pause_trigger(
        db=db,
        trigger_id=trigger_id,
        organization_id=org_uuid
    )
    return trigger


@router.post("/{id}/triggers/{trigger_id}/resume", status_code=status.HTTP_200_OK)
async def resume_agent_trigger(
    id: UUID,
    trigger_id: UUID,
    current_user: User = Depends(get_current_user),
    org_id: str = Depends(resolve_organization_id),
    db: AsyncSession = Depends(get_db_session)
):
    """Resumes a Cognitive Agent trigger."""
    from app.agents.cognitive_triggers import CognitiveAgentTriggerService
    org_uuid = UUID(org_id) if isinstance(org_id, str) else org_id
    trigger = await CognitiveAgentTriggerService.resume_trigger(
        db=db,
        trigger_id=trigger_id,
        organization_id=org_uuid
    )
    return trigger


@router.delete("/{id}/triggers/{trigger_id}", status_code=status.HTTP_200_OK)
async def delete_agent_trigger(
    id: UUID,
    trigger_id: UUID,
    current_user: User = Depends(get_current_user),
    org_id: str = Depends(resolve_organization_id),
    db: AsyncSession = Depends(get_db_session)
):
    """Deletes/disables a Cognitive Agent trigger."""
    from app.agents.cognitive_triggers import CognitiveAgentTriggerService
    org_uuid = UUID(org_id) if isinstance(org_id, str) else org_id
    success = await CognitiveAgentTriggerService.delete_trigger(
        db=db,
        trigger_id=trigger_id,
        organization_id=org_uuid
    )
    return {"success": success, "message": "Trigger deleted successfully."}


# ==========================================
# CA-07 Outputs & Provenance Endpoints
# ==========================================

@router.get("/{id}/outputs", response_model=List[CognitiveAgentOutputResponse], status_code=status.HTTP_200_OK)
async def list_agent_outputs(
    id: UUID,
    current_user: User = Depends(get_current_user),
    org_id: str = Depends(resolve_organization_id),
    db: AsyncSession = Depends(get_db_session)
):
    """Lists persistent output records generated by a specific Cognitive Agent."""
    org_uuid = UUID(org_id) if isinstance(org_id, str) else org_id
    outputs = await CognitiveAgentService.list_agent_outputs(
        db=db,
        current_user=current_user,
        agent_id=id,
        organization_id=org_uuid
    )
    return outputs


@router.get("/{id}/outputs/{output_id}", response_model=CognitiveAgentOutputResponse, status_code=status.HTTP_200_OK)
async def get_agent_output_detail(
    id: UUID,
    output_id: UUID,
    current_user: User = Depends(get_current_user),
    org_id: str = Depends(resolve_organization_id),
    db: AsyncSession = Depends(get_db_session)
):
    """Retrieves full details of a specific Cognitive Agent output with revalidated provenance."""
    org_uuid = UUID(org_id) if isinstance(org_id, str) else org_id
    output = await CognitiveAgentService.get_agent_output_detail(
        db=db,
        current_user=current_user,
        agent_id=id,
        output_id=output_id,
        organization_id=org_uuid
    )
    return output


@router.get("/{id}/executions/{execution_id}/output", response_model=Optional[CognitiveAgentOutputResponse], status_code=status.HTTP_200_OK)
async def get_execution_output(
    id: UUID,
    execution_id: UUID,
    current_user: User = Depends(get_current_user),
    org_id: str = Depends(resolve_organization_id),
    db: AsyncSession = Depends(get_db_session)
):
    """Retrieves the output record associated with a specific execution ID."""
    org_uuid = UUID(org_id) if isinstance(org_id, str) else org_id
    output = await CognitiveAgentService.get_execution_output(
        db=db,
        current_user=current_user,
        agent_id=id,
        execution_id=execution_id,
        organization_id=org_uuid
    )
    return output


# ==========================================
# CA-09 Cognitive Agent Memory Endpoints
# ==========================================

@router.get("/{id}/memories", status_code=status.HTTP_200_OK)
async def list_agent_memories(
    id: UUID,
    current_user: User = Depends(get_current_user),
    org_id: str = Depends(resolve_organization_id),
    db: AsyncSession = Depends(get_db_session)
):
    """Lists active durable memories for a Cognitive Agent."""
    from app.agents.cognitive_memory import CognitiveAgentMemoryService
    org_uuid = UUID(org_id) if isinstance(org_id, str) else org_id
    
    # IDOR Check: Ensure agent exists and belongs to org
    agent = await CognitiveAgentService.get_agent(db=db, agent_id=id, organization_id=org_uuid)
    
    memories = await CognitiveAgentMemoryService.list_agent_memories(
        db=db,
        agent_id=id,
        organization_id=org_uuid,
        workspace_id=agent.workspace_id
    )
    return [
        {
            "id": str(m.id),
            "agent_id": str(m.agent_id),
            "memory_type": m.memory_type,
            "status": m.status,
            "key": m.key,
            "content": m.content,
            "confidence": m.confidence,
            "confidence_level": m.confidence_level,
            "source_execution_id": str(m.source_execution_id) if m.source_execution_id else None,
            "source_output_id": str(m.source_output_id) if m.source_output_id else None,
            "created_at": m.created_at.isoformat() if m.created_at else None
        }
        for m in memories
    ]


@router.delete("/{id}/memories/{memory_id}", status_code=status.HTTP_200_OK)
async def delete_agent_memory(
    id: UUID,
    memory_id: UUID,
    current_user: User = Depends(get_current_user),
    org_id: str = Depends(resolve_organization_id),
    db: AsyncSession = Depends(get_db_session)
):
    """Soft-deletes a specific agent memory record."""
    from app.agents.cognitive_memory import CognitiveAgentMemoryService
    from app.agents.cognitive_audit import CognitiveAgentAuditService
    org_uuid = UUID(org_id) if isinstance(org_id, str) else org_id

    # IDOR Check: Ensure agent exists and belongs to org
    agent = await CognitiveAgentService.get_agent(db=db, agent_id=id, organization_id=org_uuid)

    success = await CognitiveAgentMemoryService.delete_memory(
        db=db,
        agent_id=id,
        memory_id=memory_id,
        organization_id=org_uuid
    )
    if success:
        await CognitiveAgentAuditService.record_agent_event(
            db=db,
            user=current_user,
            organization_id=org_uuid,
            workspace_id=agent.workspace_id,
            event_type="MEMORY_DELETED",
            agent_id=id,
            target_id=str(memory_id),
            reason=f"User deleted memory {memory_id}"
        )
    return {"success": success, "message": "Memory deleted successfully."}




