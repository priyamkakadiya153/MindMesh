import logging
from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Any
from uuid import UUID
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update

from app.core.database import get_db_session
from app.api.dependencies import get_current_user
from app.authorization.organization_resolver import resolve_organization_id
from app.models.user import User
from app.models.proactive_suggestion import ProactiveSuggestion
from app.actions.candidate import ActionCandidate, CandidateStatus
from .detection_engine import ProactiveDetectionEngine

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/proactive/action-detection", tags=["AUTO-01 Proactive Action & Deadline Detection"])

class ActionDetectionRequest(BaseModel):
    text: str
    source_type: str = "DIRECT_MESSAGE"
    conversation_id: str
    message_id: Optional[str] = None
    sender_name: Optional[str] = None
    history: Optional[List[Dict[str, Any]]] = None
    workspace_id: Optional[UUID] = None
    message_timestamp: Optional[datetime] = None

class ProactiveSuggestionResponse(BaseModel):
    id: UUID
    organization_id: Optional[UUID] = None
    workspace_id: Optional[UUID] = None
    source_type: str
    conversation_id: str
    message_id: Optional[str] = None
    detected_action_type: str
    title: str
    description: Optional[str] = None
    deadline: Optional[str] = None
    normalized_deadline: Optional[datetime] = None
    assignee_name: Optional[str] = None
    confidence: float
    confidence_level: str
    status: str
    source_label: Optional[str] = None
    source_content: Optional[str] = None
    pending_proposal: Optional[Dict[str, Any]] = None
    agent_id: Optional[UUID] = None
    agent_execution_id: Optional[UUID] = None
    agent_output_id: Optional[UUID] = None
    created_at: datetime

class PromoteSuggestionRequest(BaseModel):
    target_action_type: str = "TASK" # TASK or REMINDER

@router.post("/detect", status_code=status.HTTP_200_OK)
async def detect_actionable_signal(
    payload: ActionDetectionRequest,
    current_user: User = Depends(get_current_user),
    org_id: Optional[UUID] = Depends(resolve_organization_id),
    db: AsyncSession = Depends(get_db_session)
):
    """
    Asynchronously detects actionable commitments, deadlines, and follow-ups from conversation text.
    Returns structured ActionCandidate without executing any downstream actions.
    Prevents duplicate candidates and creates a candidate record if confidence >= MEDIUM.
    """
    candidate: ActionCandidate = ProactiveDetectionEngine.detect_candidate_action(
        text=payload.text,
        history=payload.history,
        source_type=payload.source_type,
        conversation_id=payload.conversation_id,
        message_id=payload.message_id,
        sender_id=None,
        sender_name=payload.sender_name or current_user.username or current_user.full_name,
        current_user_id=str(current_user.id),
        current_user_name=current_user.username or current_user.full_name,
        workspace_id=str(payload.workspace_id) if payload.workspace_id else (str(current_user.current_workspace_id) if current_user.current_workspace_id else None),
        message_timestamp=payload.message_timestamp
    )

    if candidate.confidence_level == "LOW" or candidate.intent.value in ("NO_ACTION", "INFORMATION_ONLY", "GENERAL_CONVERSATION", "COMPLETION_SIGNAL"):
        return {
            "detected": False,
            "intent": candidate.intent.value,
            "confidence_level": candidate.confidence_level.value,
            "candidate": candidate.model_dump(mode="json"),
            "suggestion": None
        }

    # Deduplication Check per User
    stmt = select(ProactiveSuggestion).where(
        ProactiveSuggestion.user_id == current_user.id,
        ProactiveSuggestion.detected_action_hash == candidate.detected_action_hash,
        ProactiveSuggestion.status.in_(["DETECTED", "PENDING", "PENDING_CONFIRMATION", "SHOWN", "DISMISSED", "ACCEPTED"])
    )
    res = await db.execute(stmt)
    existing = res.scalar_one_or_none()
    if existing:
        logger.info(f"Duplicate candidate action suggestion blocked for user {current_user.id} and hash {candidate.detected_action_hash}")
        import json
        existing_sug_resp = None
        if existing.status in ("DETECTED", "PENDING", "PENDING_CONFIRMATION", "SHOWN"):
            pending_prop = None
            if existing.pending_proposal_payload:
                try:
                    pending_prop = json.loads(existing.pending_proposal_payload)
                except Exception:
                    pass
            existing_sug_resp = ProactiveSuggestionResponse(
                id=existing.id,
                organization_id=existing.organization_id,
                workspace_id=existing.workspace_id,
                source_type=existing.source_type,
                conversation_id=existing.conversation_id,
                message_id=existing.message_id,
                detected_action_type=existing.detected_action_type,
                title=existing.title,
                description=existing.description,
                deadline=existing.deadline,
                normalized_deadline=existing.normalized_deadline,
                assignee_name=existing.assignee_name,
                confidence=existing.confidence,
                confidence_level=existing.confidence_level,
                status=existing.status,
                source_label=existing.source_label,
                source_content=existing.source_content,
                pending_proposal=pending_prop,
                created_at=existing.created_at
            )
        return {
            "detected": True,
            "duplicate": True,
            "intent": candidate.intent.value,
            "candidate": candidate.model_dump(mode="json"),
            "suggestion": existing_sug_resp
        }

    # Format human provenance source label
    source_label = f"From: {payload.source_type.replace('_', ' ').title()}"
    if payload.sender_name:
        source_label += f" ({payload.sender_name})"

    suggestion = ProactiveSuggestion(
        organization_id=org_id,
        workspace_id=payload.workspace_id or current_user.current_workspace_id,
        user_id=current_user.id,
        source_type=payload.source_type,
        conversation_id=payload.conversation_id,
        message_id=payload.message_id,
        detected_action_type=candidate.candidate_type or candidate.action_type.value,
        title=candidate.subject or payload.text,
        description=candidate.description,
        deadline=candidate.deadline,
        normalized_deadline=candidate.normalized_deadline.replace(tzinfo=None) if candidate.normalized_deadline else None,
        assignee_name=candidate.assignee_name,
        confidence=candidate.confidence,
        confidence_level=candidate.confidence_level.value,
        status="DETECTED",
        detected_action_hash=candidate.detected_action_hash,
        source_label=source_label,
        source_content=payload.text
    )

    db.add(suggestion)
    await db.commit()
    await db.refresh(suggestion)

    sug_resp = ProactiveSuggestionResponse(
        id=suggestion.id,
        organization_id=suggestion.organization_id,
        workspace_id=suggestion.workspace_id,
        source_type=suggestion.source_type,
        conversation_id=suggestion.conversation_id,
        message_id=suggestion.message_id,
        detected_action_type=suggestion.detected_action_type,
        title=suggestion.title,
        description=suggestion.description,
        deadline=suggestion.deadline,
        normalized_deadline=suggestion.normalized_deadline,
        assignee_name=suggestion.assignee_name,
        confidence=suggestion.confidence,
        confidence_level=suggestion.confidence_level,
        status=suggestion.status,
        source_label=suggestion.source_label,
        source_content=suggestion.source_content,
        pending_proposal=None,
        created_at=suggestion.created_at
    )

    # Emit real-time WebSocket event for proactive action popup
    try:
        from app.websocket.manager import manager
        ws_event = {
            "event": "proactive_action_detected",
            "conversation_id": suggestion.conversation_id,
            "message_id": suggestion.message_id,
            "suggestion": sug_resp.model_dump(mode="json")
        }
        await manager.send_personal_message(ws_event, str(current_user.id))
    except Exception as e:
        logger.warning(f"Failed to send WS event for proactive action: {e}")

    return {
        "detected": True,
        "duplicate": False,
        "intent": candidate.intent.value,
        "candidate": candidate.model_dump(mode="json"),
        "suggestion": sug_resp
    }

@router.get("/count", status_code=status.HTTP_200_OK)
async def get_pending_suggestions_count(
    current_user: User = Depends(get_current_user),
    org_id: Optional[UUID] = Depends(resolve_organization_id),
    db: AsyncSession = Depends(get_db_session)
):
    """Returns the total number of unresolved pending proactive action candidates for the current user."""
    now_utc = datetime.utcnow()

    # Expire outdated suggestions whose deadline has passed
    expire_stmt = (
        update(ProactiveSuggestion)
        .where(
            ProactiveSuggestion.status.in_(["DETECTED", "PENDING", "PENDING_CONFIRMATION", "SHOWN"]),
            ProactiveSuggestion.normalized_deadline.isnot(None),
            ProactiveSuggestion.normalized_deadline < now_utc
        )
        .values(status="EXPIRED")
    )
    await db.execute(expire_stmt)
    await db.commit()

    stmt = select(ProactiveSuggestion).where(
        ProactiveSuggestion.user_id == current_user.id,
        ProactiveSuggestion.status.in_(["DETECTED", "PENDING", "PENDING_CONFIRMATION", "SHOWN"]),
        ProactiveSuggestion.is_active == True
    )
    res = await db.execute(stmt)
    items = res.scalars().all()
    return {"pending_count": len(items)}

@router.get("/suggestions", status_code=status.HTTP_200_OK, response_model=List[ProactiveSuggestionResponse])
async def list_proactive_suggestions(
    conversation_id: Optional[str] = Query(None),
    source_type: Optional[str] = Query(None),
    status_filter: str = Query("DETECTED"),
    current_user: User = Depends(get_current_user),
    org_id: Optional[UUID] = Depends(resolve_organization_id),
    db: AsyncSession = Depends(get_db_session)
):
    """Lists candidate proactive suggestions with flexible status and source filtering."""
    import json
    now_utc = datetime.utcnow()

    # Expire outdated suggestions whose deadline has passed
    expire_stmt = (
        update(ProactiveSuggestion)
        .where(
            ProactiveSuggestion.status.in_(["DETECTED", "PENDING", "PENDING_CONFIRMATION", "SHOWN"]),
            ProactiveSuggestion.normalized_deadline.isnot(None),
            ProactiveSuggestion.normalized_deadline < now_utc
        )
        .values(status="EXPIRED")
    )
    await db.execute(expire_stmt)
    await db.commit()

    stmt = select(ProactiveSuggestion).where(
        ProactiveSuggestion.user_id == current_user.id,
        ProactiveSuggestion.is_active == True
    )
    if conversation_id:
        stmt = stmt.where(ProactiveSuggestion.conversation_id == conversation_id)
    if source_type and source_type.upper() != "ALL":
        stmt = stmt.where(ProactiveSuggestion.source_type == source_type)

    if status_filter:
        s_upper = status_filter.upper()
        if s_upper in ("DETECTED", "PENDING", "NEEDS_ATTENTION"):
            stmt = stmt.where(ProactiveSuggestion.status.in_(["DETECTED", "PENDING", "PENDING_CONFIRMATION", "SHOWN"]))
        elif s_upper in ("ACCEPTED", "RESOLVED", "COMPLETED"):
            stmt = stmt.where(ProactiveSuggestion.status.in_(["ACCEPTED", "RESOLVED"]))
        elif s_upper == "DISMISSED":
            stmt = stmt.where(ProactiveSuggestion.status == "DISMISSED")
        elif s_upper == "EXPIRED":
            stmt = stmt.where(ProactiveSuggestion.status == "EXPIRED")
        elif s_upper != "ALL":
            stmt = stmt.where(ProactiveSuggestion.status == status_filter)

    stmt = stmt.order_by(ProactiveSuggestion.created_at.desc()).limit(50)
    res = await db.execute(stmt)
    items = res.scalars().all()

    result_list = []
    for item in items:
        pending_prop = None
        if item.pending_proposal_payload:
            try:
                pending_prop = json.loads(item.pending_proposal_payload)
            except Exception:
                pass
        result_list.append(
            ProactiveSuggestionResponse(
                id=item.id,
                organization_id=item.organization_id,
                workspace_id=item.workspace_id,
                source_type=item.source_type,
                conversation_id=item.conversation_id,
                message_id=item.message_id,
                detected_action_type=item.detected_action_type,
                title=item.title,
                description=item.description,
                deadline=item.deadline,
                normalized_deadline=item.normalized_deadline,
                assignee_name=item.assignee_name,
                confidence=item.confidence,
                confidence_level=item.confidence_level,
                status=item.status,
                source_label=item.source_label,
                source_content=item.source_content,
                pending_proposal=pending_prop,
                agent_id=getattr(item, "agent_id", None),
                agent_execution_id=getattr(item, "agent_execution_id", None),
                agent_output_id=getattr(item, "agent_output_id", None),
                created_at=item.created_at
            )
        )

    return result_list

@router.post("/suggestions/{suggestion_id}/dismiss", status_code=status.HTTP_200_OK)
async def dismiss_proactive_suggestion(
    suggestion_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Dismisses a candidate proactive suggestion so it won't be shown again."""
    stmt = select(ProactiveSuggestion).where(
        ProactiveSuggestion.id == suggestion_id,
        ProactiveSuggestion.user_id == current_user.id
    )
    res = await db.execute(stmt)
    item = res.scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=404, detail="Suggestion not found")

    item.status = "DISMISSED"
    item.dismissed_at = datetime.utcnow()
    item.pending_proposal_payload = None
    item.pending_target_action_type = None
    await db.commit()

    return {"status": "DISMISSED", "id": str(suggestion_id)}

@router.post("/suggestions/{suggestion_id}/promote", status_code=status.HTTP_200_OK)
async def promote_suggestion_to_action_proposal(
    suggestion_id: UUID,
    req: PromoteSuggestionRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """
    Promotes a candidate proactive suggestion into a PENDING_CONFIRMATION AUTO-06 ActionProposal.
    The proposal persists across navigations until confirmed or cancelled by the user.
    """
    import json
    stmt = select(ProactiveSuggestion).where(
        ProactiveSuggestion.id == suggestion_id,
        ProactiveSuggestion.user_id == current_user.id
    )
    res = await db.execute(stmt)
    item = res.scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=404, detail="Suggestion not found")

    target_type = req.target_action_type.upper()
    if target_type in ("REMINDER", "CREATE_REMINDER"):
        intent_type = "CREATE_REMINDER"
    else:
        intent_type = "CREATE_TASK"

    params = {
        "title": item.title,
        "reminder_text": item.title,
        "raw_query": item.title,
        "due_date_str": item.deadline,
        "time_str": item.deadline or "tomorrow",
        "due_date": item.normalized_deadline.isoformat() if item.normalized_deadline else None,
        "assignee_name": item.assignee_name,
        "source_type": item.source_type,
        "conversation_id": item.conversation_id,
        "message_id": item.message_id,
        "suggestion_id": str(item.id)
    }

    proposal = {
        "proposal_id": f"prop-{item.id}",
        "intent_type": intent_type,
        "title": f"Action Proposal: {item.title}",
        "description": f"Extracted from conversation signal ({item.detected_action_type}). Deadline: {item.deadline or 'None'}",
        "parameters": params,
        "confirmation_required": True
    }

    item.status = "PENDING_CONFIRMATION"
    item.pending_target_action_type = intent_type
    item.pending_proposal_payload = json.dumps(proposal)
    await db.commit()

    return {
        "status": "PENDING_CONFIRMATION",
        "suggestion_id": str(suggestion_id),
        "proposal": proposal
    }

@router.post("/suggestions/{suggestion_id}/cancel_proposal", status_code=status.HTTP_200_OK)
async def cancel_suggestion_proposal(
    suggestion_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Cancels a pending action proposal, reverting suggestion status back to DETECTED."""
    stmt = select(ProactiveSuggestion).where(
        ProactiveSuggestion.id == suggestion_id,
        ProactiveSuggestion.user_id == current_user.id
    )
    res = await db.execute(stmt)
    item = res.scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=404, detail="Suggestion not found")

    item.status = "DETECTED"
    item.pending_target_action_type = None
    item.pending_proposal_payload = None
    await db.commit()

    return {"status": "DETECTED", "suggestion_id": str(suggestion_id)}
