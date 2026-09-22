import asyncio
from typing import Dict, Set, List, Optional
from fastapi import WebSocket
from datetime import datetime, timedelta
from dataclasses import dataclass
from uuid import uuid4
import json
import logging
from .presence_service import presence_service

logger = logging.getLogger("mindmesh.websocket")

@dataclass
class ConnectionSession:
    connection_id: str
    user_id: str
    organization_id: str
    workspace_id: Optional[str]
    websocket: WebSocket
    connected_at: datetime
    last_heartbeat: datetime

class ConnectionManager:
    def __init__(self):
        # Maps user_id -> Dict[connection_id, ConnectionSession]
        self.user_sessions: Dict[str, Dict[str, ConnectionSession]] = {}
        # Background cleanup task handle
        self._cleanup_task: Optional[asyncio.Task] = None

    async def start_heartbeat_sweeper(self):
        if self._cleanup_task is None or self._cleanup_task.done():
            self._cleanup_task = asyncio.create_task(self._sweep_loop())

    async def _sweep_loop(self):
        while True:
            try:
                await asyncio.sleep(20)
                await self.sweep_stale_connections()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in heartbeat sweeper: {e}")

    async def sweep_stale_connections(self):
        now = datetime.utcnow()
        threshold = now - timedelta(seconds=60)
        stale_list = []

        for user_id, sessions in list(self.user_sessions.items()):
            for conn_id, session in list(sessions.items()):
                if session.last_heartbeat < threshold:
                    stale_list.append((user_id, conn_id, session.websocket))

        for user_id, conn_id, ws in stale_list:
            logger.info(f"Sweeping stale connection {conn_id} for user {user_id}")
            try:
                await ws.close(code=1000, reason="Heartbeat timeout")
            except Exception:
                pass
            self.disconnect(ws, user_id, conn_id)

    async def sync_and_broadcast_presence(self, user_id: str, status: str, last_seen_iso: str):
        try:
            from uuid import UUID
            from ..database.session import AsyncSessionLocal
            from ..models.conversations import UserPresence
            from sqlalchemy import select

            u_id = UUID(user_id)
            now = datetime.utcnow()
            async with AsyncSessionLocal() as db:
                p_stmt = select(UserPresence).where(UserPresence.user_id == u_id)
                p_res = await db.execute(p_stmt)
                pres = p_res.scalar_one_or_none()
                if pres:
                    pres.status = status
                    pres.last_seen = now
                else:
                    db.add(UserPresence(user_id=u_id, status=status, last_seen=now))
                await db.commit()
        except Exception as e:
            logger.error(f"Error syncing presence in DB: {e}")

        msg = {
            "event": "presence_updated",
            "user_id": str(user_id),
            "status": status,
            "last_seen": last_seen_iso
        }
        all_user_ids = list(self.user_sessions.keys())
        for uid in all_user_ids:
            await self.send_personal_message(msg, str(uid))

    async def connect(
        self,
        websocket: WebSocket,
        user_id: str,
        organization_id: str,
        workspace_id: Optional[str] = None
    ) -> ConnectionSession:
        await websocket.accept()
        conn_id = str(uuid4())
        now = datetime.utcnow()

        session = ConnectionSession(
            connection_id=conn_id,
            user_id=user_id,
            organization_id=organization_id,
            workspace_id=workspace_id,
            websocket=websocket,
            connected_at=now,
            last_heartbeat=now
        )

        was_offline = (user_id not in self.user_sessions) or (len(self.user_sessions[user_id]) == 0)

        if user_id not in self.user_sessions:
            self.user_sessions[user_id] = {}
        self.user_sessions[user_id][conn_id] = session

        if was_offline:
            asyncio.create_task(self.sync_and_broadcast_presence(user_id, "online", p_info["last_seen"]))

        # Send initial presence of all currently online users to the newly connected socket
        for online_uid, sessions in list(self.user_sessions.items()):
            if str(online_uid).lower() != str(user_id).lower() and len(sessions) > 0:
                p_data = presence_service.get_user_presence(str(online_uid))
                if p_data.get("status") == "online":
                    try:
                        await websocket.send_text(json.dumps({
                            "event": "presence_updated",
                            "user_id": str(online_uid),
                            "status": "online",
                            "last_seen": p_data.get("last_seen", now.isoformat())
                        }))
                    except Exception:
                        pass

        # Start sweeper if not running
        await self.start_heartbeat_sweeper()
        return session

    def update_heartbeat(self, user_id: str, connection_id: str):
        u_str = str(user_id).lower()
        for uid_key in list(self.user_sessions.keys()):
            if str(uid_key).lower() == u_str:
                if connection_id in self.user_sessions[uid_key]:
                    self.user_sessions[uid_key][connection_id].last_heartbeat = datetime.utcnow()

    def disconnect(self, websocket: WebSocket, user_id: str, connection_id: Optional[str] = None):
        u_str = str(user_id).lower()
        matching_keys = [k for k in list(self.user_sessions.keys()) if str(k).lower() == u_str]
        for k in matching_keys:
            if connection_id and connection_id in self.user_sessions[k]:
                del self.user_sessions[k][connection_id]
            else:
                to_del = [cid for cid, s in self.user_sessions[k].items() if s.websocket == websocket]
                for cid in to_del:
                    del self.user_sessions[k][cid]

            if not self.user_sessions.get(k):
                if k in self.user_sessions:
                    del self.user_sessions[k]
                p_info = presence_service.mark_user_offline(str(user_id))
                asyncio.create_task(self.sync_and_broadcast_presence(str(user_id), "offline", p_info["last_seen"]))

    async def send_personal_message(self, message: dict, user_id: str):
        u_str = str(user_id).lower()
        matching_keys = [k for k in list(self.user_sessions.keys()) if str(k).lower() == u_str]
        for k in matching_keys:
            stale_conns = []
            for conn_id, session in list(self.user_sessions[k].items()):
                try:
                    await session.websocket.send_text(json.dumps(message))
                except Exception as e:
                    logger.warning(f"Failed sending WS event to user {user_id} session {conn_id}: {e}")
                    stale_conns.append((session.websocket, k, conn_id))
            for ws, k_key, conn_id in stale_conns:
                self.disconnect(ws, k_key, conn_id)

    async def broadcast_to_users(self, message: dict, user_ids: List[str]):
        for uid in user_ids:
            await self.send_personal_message(message, str(uid))

    def get_presence(self, user_id: str) -> dict:
        return presence_service.get_user_presence(user_id)

    def set_presence(self, user_id: str, status: str, custom_status: Optional[str] = None) -> dict:
        return presence_service.set_user_presence(user_id, status, custom_status)

manager = ConnectionManager()
