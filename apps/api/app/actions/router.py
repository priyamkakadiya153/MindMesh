import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db_session
from app.core.dependencies import get_current_user
from app.models.user import User
from .types import ActionConfirmRequest, ActionResult, ActionResultStatus, ActionProposal, ActionIntentType, ActionStatus
from .registry import action_registry

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/actions", tags=["MindMesh Action & Intent Engine"])

# Idempotency cache to prevent rapid double-clicks creating duplicate tasks
_EXECUTED_PROPOSALS = set()

@router.post("/confirm", status_code=status.HTTP_200_OK, response_model=ActionResult)
async def confirm_action_proposal(
    req: ActionConfirmRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Executes or cancels an Action Proposal based on user confirmation."""
    proposal_id = req.proposal_id

    # 1. Check Cancellation
    if not req.confirm:
        logger.info(f"Action proposal {proposal_id} cancelled by user {current_user.email}")
        cancel_result = ActionResult(
            status=ActionResultStatus.CANCELLED,
            action_type=req.intent_type,
            message="Action proposal cancelled. Nothing was changed in your workspace.",
            metadata={"proposal_id": proposal_id}
        )
        from .audit_service import AuditService
        cancel_proposal = ActionProposal(
            proposal_id=proposal_id,
            intent_type=req.intent_type,
            title=req.parameters.get("title", "Workspace Action"),
            parameters=req.parameters,
            workspace_id=str(req.workspace_id or current_user.current_workspace_id or ""),
            user_id=str(current_user.id),
            confirmation_required=True,
            status=ActionStatus.CANCELLED
        )
        await AuditService.record_action_event(cancel_proposal, cancel_result, current_user, db, source_type="AI_CHAT")

        # Reset associated proactive suggestion status back to DETECTED
        suggestion_id_str = req.parameters.get("suggestion_id") or (proposal_id.replace("prop-", "") if proposal_id.startswith("prop-") else None)
        if suggestion_id_str:
            try:
                from uuid import UUID
                from sqlalchemy import select
                from app.models.proactive_suggestion import ProactiveSuggestion
                s_stmt = select(ProactiveSuggestion).where(
                    ProactiveSuggestion.id == UUID(suggestion_id_str),
                    ProactiveSuggestion.user_id == current_user.id
                )
                s_res = await db.execute(s_stmt)
                s_item = s_res.scalar_one_or_none()
                if s_item:
                    s_item.status = "DETECTED"
                    s_item.pending_proposal_payload = None
                    s_item.pending_target_action_type = None
                    await db.commit()
            except Exception as e:
                logger.warning(f"Failed to reset proactive suggestion on cancellation: {e}")

        return cancel_result

    # 2. Idempotency Check (Duplicate Execution Prevention)
    if proposal_id in _EXECUTED_PROPOSALS:
        logger.warning(f"Duplicate confirmation attempt blocked for proposal {proposal_id}")
        return ActionResult(
            status=ActionResultStatus.SUCCESS,
            action_type=req.intent_type,
            message="This action has already been completed.",
            metadata={"proposal_id": proposal_id, "duplicate_blocked": True}
        )

    # 3. Build ActionProposal object from confirmation payload
    from datetime import datetime, timezone
    created_at_val = datetime.now(timezone.utc)
    if req.parameters.get("created_at"):
        try:
            created_at_val = datetime.fromisoformat(req.parameters["created_at"])
        except Exception:
            pass

    proposal = ActionProposal(
        proposal_id=proposal_id,
        intent_type=req.intent_type,
        title=req.parameters.get("title", "Workspace Action"),
        parameters=req.parameters,
        workspace_id=str(req.workspace_id or current_user.current_workspace_id or ""),
        user_id=str(current_user.id),
        confirmation_required=True,
        status=ActionStatus.CONFIRMED,
        created_at=created_at_val
    )

    # 4. Expiration Validation Check
    from .safety_guard import ActionSafetyGuard
    from .audit_service import AuditService

    is_valid_exp, exp_err = ActionSafetyGuard.validate_expiration(proposal)
    if not is_valid_exp:
        logger.warning(f"Expired action proposal attempt: {proposal_id}")
        exp_result = ActionResult(
            status=ActionResultStatus.FAILED,
            action_type=req.intent_type,
            message=exp_err or "Action proposal expired.",
            error_code="PROPOSAL_EXPIRED"
        )
        await AuditService.record_action_event(proposal, exp_result, current_user, db, source_type="AI_CHAT")
        return exp_result

    # 5. Workspace Scope Isolation Check
    is_valid_ws, ws_err = ActionSafetyGuard.validate_workspace_scope(proposal, current_user)
    if not is_valid_ws:
        logger.warning(f"Workspace scope mismatch for proposal {proposal_id}")
        return ActionResult(
            status=ActionResultStatus.NOT_AUTHORIZED,
            action_type=req.intent_type,
            message=ws_err or "Workspace mismatch.",
            error_code="WORKSPACE_MISMATCH"
        )

    # 6. Destructive Action Protection Check
    if req.intent_type == ActionIntentType.DELETE_DOCUMENT or req.parameters.get("is_blocked"):
        return ActionResult(
            status=ActionResultStatus.FAILED,
            action_type=req.intent_type,
            message="I can't perform destructive actions like that through MindMesh AI.",
            error_code="DESTRUCTIVE_ACTION_BLOCKED"
        )

    # 7. Dispatch to Action Executor
    result = await action_registry.dispatch(proposal, current_user, db)

    # 8. Post-Execution Verification Check
    result = await ActionSafetyGuard.verify_post_execution(proposal, result, current_user, db)

    if result.status == ActionResultStatus.SUCCESS:
        _EXECUTED_PROPOSALS.add(proposal_id)
        suggestion_id_str = req.parameters.get("suggestion_id") or (proposal_id.replace("prop-", "") if proposal_id.startswith("prop-") else None)
        if suggestion_id_str:
            try:
                from uuid import UUID
                from sqlalchemy import select
                from app.models.proactive_suggestion import ProactiveSuggestion
                s_stmt = select(ProactiveSuggestion).where(
                    ProactiveSuggestion.id == UUID(suggestion_id_str),
                    ProactiveSuggestion.user_id == current_user.id
                )
                s_res = await db.execute(s_stmt)
                s_item = s_res.scalar_one_or_none()
                if s_item:
                    s_item.status = "ACCEPTED"
                    s_item.pending_proposal_payload = None
                    s_item.pending_target_action_type = None
                    if result.metadata and result.metadata.get("task_id"):
                        try:
                            s_item.executed_action_id = UUID(str(result.metadata["task_id"]))
                        except Exception:
                            pass
                    await db.commit()
            except Exception as e:
                logger.warning(f"Failed to update proactive suggestion status on execution success: {e}")

    # 9. Record Authoritative Action Audit Event (AUTO-07)
    await AuditService.record_action_event(
        proposal=proposal,
        result=result,
        user=current_user,
        db=db,
        source_type=req.parameters.get("source_type", "AI_CHAT")
    )

    return result
