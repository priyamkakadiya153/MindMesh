from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from typing import Optional, Dict
import json
import logging
from datetime import datetime
from uuid import UUID

from .manager import manager
from .typing_service import typing_service
from .presence_service import presence_service
from ..core.config import settings
from ..core.security import decode_token_payload
from ..database.session import AsyncSessionLocal
from ..models.user import User
from ..models.conversations import UserPresence, ConversationMember, DirectMessage, MessageRead

logger = logging.getLogger("mindmesh.websocket.router")

router = APIRouter()

async def authenticate_ws_token(token: str) -> Optional[dict]:
    if not token:
        return None
    try:
        payload = decode_token_payload(token, settings.JWT_SECRET)
        if not payload:
            return None
        user_id_str = payload.get("sub")
        if not user_id_str:
            return None
        
        async with AsyncSessionLocal() as db:
            stmt = select(User).where(User.id == UUID(user_id_str), User.is_active == True, User.deleted_at == None)
            res = await db.execute(stmt)
            user = res.scalar_one_or_none()
            if not user:
                return None
            return {
                "user": user,
                "user_id": str(user.id),
                "org_id": payload.get("org_id", ""),
                "workspace_id": payload.get("workspace_id")
            }
    except Exception as e:
        logger.error(f"WS authentication error: {e}")
        return None

async def verify_conversation_membership(db: AsyncSession, conversation_id: UUID, user_id: UUID) -> bool:
    stmt = select(ConversationMember).where(
        ConversationMember.conversation_id == conversation_id,
        ConversationMember.user_id == user_id
    )
    res = await db.execute(stmt)
    return res.scalar_one_or_none() is not None

@router.websocket("/ws/chat")
async def websocket_chat_endpoint(
    websocket: WebSocket,
    token: Optional[str] = Query(None),
    organization_id: Optional[str] = Query(None),
    workspace_id: Optional[str] = Query(None)
):
    auth_data = await authenticate_ws_token(token)
    if not auth_data:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    user = auth_data["user"]
    user_id_str = auth_data["user_id"]
    org_id_str = organization_id or auth_data["org_id"]
    ws_id_str = workspace_id or auth_data["workspace_id"]

    session = await manager.connect(websocket, user_id_str, org_id_str, ws_id_str)

    # Send connection acknowledgment
    await websocket.send_text(json.dumps({
        "event": "connected",
        "connection_id": session.connection_id,
        "user_id": user_id_str,
        "organization_id": org_id_str,
        "timestamp": datetime.utcnow().isoformat()
    }))

    try:
        while True:
            data_str = await websocket.receive_text()
            try:
                payload = json.loads(data_str)
                event_type = payload.get("event")

                # Heartbeat Ping / Pong
                if event_type in ["ping", "heartbeat"]:
                    manager.update_heartbeat(user_id_str, session.connection_id)
                    await websocket.send_text(json.dumps({
                        "event": "heartbeat_ack",
                        "timestamp": datetime.utcnow().isoformat()
                    }))

                # Online Presence update
                elif event_type == "update_status":
                    new_status = payload.get("status", "online")
                    custom_status = payload.get("custom_status")
                    presence_info = manager.set_presence(user_id_str, new_status, custom_status)

                    async with AsyncSessionLocal() as db:
                        p_stmt = select(UserPresence).where(UserPresence.user_id == user.id)
                        p_res = await db.execute(p_stmt)
                        pres = p_res.scalar_one_or_none()
                        if pres:
                            pres.status = new_status
                            pres.custom_status = custom_status
                            pres.last_seen = datetime.utcnow()
                        else:
                            db.add(UserPresence(
                                user_id=user.id,
                                status=new_status,
                                custom_status=custom_status,
                                last_seen=datetime.utcnow()
                            ))
                        await db.commit()

                    await websocket.send_text(json.dumps({
                        "event": "presence_updated",
                        "presence": presence_info,
                        "timestamp": datetime.utcnow().isoformat()
                    }))

                # Typing Start Event
                elif event_type == "typing_start":
                    conv_id = payload.get("conversation_id")
                    if conv_id:
                        async with AsyncSessionLocal() as db:
                            is_member = await verify_conversation_membership(db, UUID(conv_id), user.id)
                            if is_member:
                                # Define auto-timeout callback
                                async def on_typing_timeout(c_id, u_id):
                                    # Fetch members to send typing_stop
                                    async with AsyncSessionLocal() as db2:
                                        m_stmt = select(ConversationMember.user_id).where(ConversationMember.conversation_id == UUID(c_id))
                                        m_res = await db2.execute(m_stmt)
                                        u_ids = [str(uid) for uid in m_res.scalars().all()]
                                        await manager.broadcast_to_users({
                                            "event": "user_typing",
                                            "conversation_id": c_id,
                                            "user_id": u_id,
                                            "user_name": user.full_name,
                                            "is_typing": False,
                                            "typing_users": typing_service.get_typing_users(c_id),
                                            "timestamp": datetime.utcnow().isoformat()
                                        }, u_ids)

                                typing_service.start_typing(conv_id, user_id_str, user.full_name, on_typing_timeout)
                                # Fetch all members of conversation
                                m_stmt = select(ConversationMember.user_id).where(ConversationMember.conversation_id == UUID(conv_id))
                                m_res = await db.execute(m_stmt)
                                member_user_ids = [str(uid) for uid in m_res.scalars().all()]

                                await manager.broadcast_to_users({
                                    "event": "user_typing",
                                    "conversation_id": conv_id,
                                    "user_id": user_id_str,
                                    "user_name": user.full_name,
                                    "is_typing": True,
                                    "typing_users": typing_service.get_typing_users(conv_id),
                                    "timestamp": datetime.utcnow().isoformat()
                                }, member_user_ids)

                # Typing Stop Event
                elif event_type == "typing_stop":
                    conv_id = payload.get("conversation_id")
                    if conv_id:
                        typing_service.stop_typing(conv_id, user_id_str)
                        async with AsyncSessionLocal() as db:
                            is_member = await verify_conversation_membership(db, UUID(conv_id), user.id)
                            if is_member:
                                m_stmt = select(ConversationMember.user_id).where(ConversationMember.conversation_id == UUID(conv_id))
                                m_res = await db.execute(m_stmt)
                                member_user_ids = [str(uid) for uid in m_res.scalars().all()]

                                await manager.broadcast_to_users({
                                    "event": "user_typing",
                                    "conversation_id": conv_id,
                                    "user_id": user_id_str,
                                    "user_name": user.full_name,
                                    "is_typing": False,
                                    "typing_users": typing_service.get_typing_users(conv_id),
                                    "timestamp": datetime.utcnow().isoformat()
                                }, member_user_ids)

                # Mark Read Event
                elif event_type == "mark_read":
                    conv_id = payload.get("conversation_id")
                    if conv_id:
                        async with AsyncSessionLocal() as db:
                            is_member = await verify_conversation_membership(db, UUID(conv_id), user.id)
                            if is_member:
                                # Update read status
                                m_stmt = select(ConversationMember).where(
                                    ConversationMember.conversation_id == UUID(conv_id),
                                    ConversationMember.user_id == user.id
                                )
                                m_res = await db.execute(m_stmt)
                                member_obj = m_res.scalar_one_or_none()
                                if member_obj:
                                    member_obj.unread_count = 0
                                    member_obj.last_read_at = datetime.utcnow()
                                    await db.commit()

                                # Broadcast read receipt to all members
                                all_m_stmt = select(ConversationMember.user_id).where(ConversationMember.conversation_id == UUID(conv_id))
                                all_m_res = await db.execute(all_m_stmt)
                                member_user_ids = [str(uid) for uid in all_m_res.scalars().all()]

                                await manager.broadcast_to_users({
                                    "event": "messages_read",
                                    "conversation_id": conv_id,
                                    "read_by_user_id": user_id_str,
                                    "read_at": datetime.utcnow().isoformat()
                                }, member_user_ids)

            except json.JSONDecodeError:
                pass
    except WebSocketDisconnect:
        manager.disconnect(websocket, user_id_str, session.connection_id)
    except Exception as e:
        logger.error(f"WS exception for user {user_id_str}: {e}")
        manager.disconnect(websocket, user_id_str, session.connection_id)

@router.websocket("/ws/presence")
async def websocket_presence_endpoint(websocket: WebSocket, token: Optional[str] = Query(None)):
    # Redirect presence to chat endpoint or keep for backward compatibility
    await websocket_chat_endpoint(websocket, token=token)

@router.websocket("/ws/typing")
async def websocket_typing_endpoint(websocket: WebSocket, token: Optional[str] = Query(None)):
    await websocket_chat_endpoint(websocket, token=token)
