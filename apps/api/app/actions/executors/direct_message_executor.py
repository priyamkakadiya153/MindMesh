import logging
from uuid import UUID, uuid4
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_, and_

from app.models.user import User
from app.models.conversations import Conversation, ConversationMember, DirectMessage
from app.notifications.models import Notification
from .base import BaseActionExecutor
from ..types import ActionProposal, ActionResult, ActionResultStatus, ActionIntentType

logger = logging.getLogger(__name__)

class DirectMessageActionExecutor(BaseActionExecutor):
    """Executes REAL database mutations to insert a DirectMessage into PostgreSQL for AUTO-03."""

    async def execute(
        self,
        proposal: ActionProposal,
        user: User,
        db: AsyncSession
    ) -> ActionResult:
        try:
            org_id = user.organization_id
            workspace_id = user.current_workspace_id

            params = proposal.parameters or {}
            recipient_name = params.get("recipient_name") or params.get("recipient") or ""
            message_body = params.get("message_body") or params.get("message") or ""

            if not message_body:
                return ActionResult(
                    status=ActionResultStatus.NEEDS_CLARIFICATION,
                    action_type=ActionIntentType.SEND_DIRECT_MESSAGE,
                    message="What message would you like me to send?",
                    error_code="MESSAGE_BODY_REQUIRED"
                )

            if not recipient_name:
                return ActionResult(
                    status=ActionResultStatus.NEEDS_CLARIFICATION,
                    action_type=ActionIntentType.SEND_DIRECT_MESSAGE,
                    message="Who would you like me to send this message to?",
                    error_code="RECIPIENT_REQUIRED"
                )

            # 1. Check for Group Conversation Resolution ("the team", "mindmesh development", etc.)
            is_group_query = any(g_kw in recipient_name.lower() for g_kw in ["team", "group", "channel", "everyone", "devs", "developers"])
            target_conv = None
            target_recipient = None
            recipient_display_name = recipient_name

            if is_group_query or "group" in params.get("target_type", "").lower():
                group_stmt = select(Conversation).where(
                    Conversation.organization_id == org_id,
                    Conversation.type.in_(["group", "channel", "project_channel"])
                )
                group_res = await db.execute(group_stmt)
                group_convs = group_res.scalars().all()
                if group_convs:
                    # Match exact or best title
                    matched_group = next((g for g in group_convs if recipient_name.lower() in (g.title or "").lower()), group_convs[0])
                    target_conv = matched_group
                    recipient_display_name = f"{target_conv.title or 'Team'} (Group)"

            # 2. Resolve Individual Member Recipient if Not Group
            if not target_conv:
                user_stmt = select(User).where(
                    or_(
                        User.first_name.ilike(f"%{recipient_name}%"),
                        User.last_name.ilike(f"%{recipient_name}%"),
                        User.username.ilike(f"%{recipient_name}%"),
                        User.email.ilike(f"%{recipient_name}%")
                    ),
                    User.id != user.id
                )
                user_res = await db.execute(user_stmt)
                matching_users = user_res.scalars().all()

                if not matching_users:
                    logger.info(f"Recipient '{recipient_name}' not found in workspace.")
                    return ActionResult(
                        status=ActionResultStatus.FAILED,
                        action_type=ActionIntentType.SEND_DIRECT_MESSAGE,
                        message=f"I couldn't find a workspace member or group matching '{recipient_name}'. Who should I send this to?",
                        error_code="RECIPIENT_NOT_FOUND"
                    )

                if len(matching_users) > 1:
                    names = ", ".join([f"{u.full_name} ({u.email})" for u in matching_users[:3]])
                    return ActionResult(
                        status=ActionResultStatus.NEEDS_CLARIFICATION,
                        action_type=ActionIntentType.SEND_DIRECT_MESSAGE,
                        message=f"I found multiple people named '{recipient_name}': {names}. Which person do you mean?",
                        error_code="AMBIGUOUS_RECIPIENT"
                    )

                target_recipient = matching_users[0]
                recipient_display_name = target_recipient.full_name

                # Resolve or Create Private DM Conversation
                conv_stmt = select(Conversation).where(
                    Conversation.organization_id == org_id,
                    Conversation.type == "private",
                    or_(
                        and_(Conversation.participant_one == user.id, Conversation.participant_two == target_recipient.id),
                        and_(Conversation.participant_one == target_recipient.id, Conversation.participant_two == user.id)
                    )
                )
                conv_res = await db.execute(conv_stmt)
                target_conv = conv_res.scalars().first()

                if not target_conv:
                    target_conv = Conversation(
                        id=uuid4(),
                        organization_id=org_id,
                        workspace_id=workspace_id,
                        type="private",
                        visibility="private",
                        participant_one=user.id,
                        participant_two=target_recipient.id,
                        owner_id=user.id,
                        created_by_user_id=user.id,
                        created_at=datetime.utcnow()
                    )
                    db.add(target_conv)
                    await db.flush()

                    # Add Members
                    m1 = ConversationMember(id=uuid4(), conversation_id=target_conv.id, user_id=user.id, role="owner", joined_at=datetime.utcnow())
                    m2 = ConversationMember(id=uuid4(), conversation_id=target_conv.id, user_id=target_recipient.id, role="member", joined_at=datetime.utcnow())
                    db.add_all([m1, m2])

            # 3. Create Real DirectMessage Record in PostgreSQL
            new_dm = DirectMessage(
                id=uuid4(),
                conversation_id=target_conv.id,
                sender_id=user.id,
                organization_id=org_id,
                workspace_id=workspace_id,
                message_type="text",
                content=message_body,
                status="sent",
                created_at=datetime.utcnow()
            )
            db.add(new_dm)

            # Update Conversation last message indicators
            target_conv.last_message_id = new_dm.id
            target_conv.last_message_at = datetime.utcnow()

            # 4. Insert Notifications for Recipient(s)
            sender_display_name = getattr(user, 'full_name', str(user.email))
            recipient_user_ids = []
            if target_recipient:
                recipient_user_ids.append(str(target_recipient.id))
                notif = Notification(
                    id=uuid4(),
                    user_id=target_recipient.id,
                    organization_id=org_id,
                    title=f"💬 New Message from {sender_display_name}",
                    message=message_body,
                    type="message",
                    priority="normal",
                    is_read=False,
                    entity_type="DIRECT_MESSAGE",
                    entity_id=new_dm.id,
                    created_at=datetime.utcnow()
                )
                db.add(notif)
            else:
                # Fetch members of group conversation for notifications & WS broadcast
                mem_stmt = select(ConversationMember).where(ConversationMember.conversation_id == target_conv.id)
                mem_res = await db.execute(mem_stmt)
                group_members = mem_res.scalars().all()
                recipient_user_ids = [str(m.user_id) for m in group_members if m.user_id != user.id]

            await db.commit()
            await db.refresh(new_dm)

            # 5. Post-Execution Persistence Verification
            verif_stmt = select(DirectMessage).where(DirectMessage.id == new_dm.id)
            verif_res = await db.execute(verif_stmt)
            persisted = verif_res.scalar_one_or_none()
            if not persisted:
                return ActionResult(
                    status=ActionResultStatus.FAILED,
                    action_type=ActionIntentType.SEND_DIRECT_MESSAGE,
                    message="I couldn't send the message because database persistence failed. Nothing was sent.",
                    error_code="PERSISTENCE_VERIFICATION_FAILED"
                )

            # 6. Real-Time WebSocket Event Broadcast
            try:
                from app.websocket.manager import manager
                ws_event = {
                    "event": "new_message",
                    "conversation_id": str(target_conv.id),
                    "message": {
                        "id": str(new_dm.id),
                        "conversation_id": str(target_conv.id),
                        "sender_id": str(user.id),
                        "content": message_body,
                        "created_at": new_dm.created_at.isoformat() if new_dm.created_at else None,
                        "status": "sent"
                    }
                }
                broadcast_users = recipient_user_ids + [str(user.id)]
                await manager.broadcast_to_users(ws_event, broadcast_users)
            except Exception as ws_err:
                logger.warning(f"WebSocket broadcast notice failed (message still saved): {str(ws_err)}")

            msg = f"Done — your message was sent to {recipient_display_name}."
            logger.info(f"[AUTO-03 REAL DM SENT SUCCESS] Sent message to {recipient_display_name} (DM ID: {new_dm.id})")

            return ActionResult(
                status=ActionResultStatus.SUCCESS,
                action_type=ActionIntentType.SEND_DIRECT_MESSAGE,
                entity_type="DIRECT_MESSAGE",
                entity_id=str(new_dm.id),
                entity_name=recipient_display_name,
                message=msg,
                metadata={
                    "message_id": str(new_dm.id),
                    "conversation_id": str(target_conv.id),
                    "recipient_id": str(target_recipient.id) if target_recipient else str(target_conv.id),
                    "recipient_name": recipient_display_name,
                    "content": message_body
                }
            )

        except Exception as e:
            logger.error(f"Failed sending direct message: {str(e)}", exc_info=True)
            await db.rollback()
            return ActionResult(
                status=ActionResultStatus.FAILED,
                action_type=ActionIntentType.SEND_DIRECT_MESSAGE,
                message="I couldn't send the message due to a backend error. Nothing was sent.",
                error_code="EXECUTION_FAILED"
            )
