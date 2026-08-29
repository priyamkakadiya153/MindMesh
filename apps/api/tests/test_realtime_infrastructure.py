import pytest
import asyncio
from uuid import uuid4
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi.testclient import TestClient

from app.main import app
from app.models.user import User
from app.models.session import UserSession
from app.models.conversations import UserPresence
from app.core.security import create_access_token
from app.websocket.manager import manager, ConnectionSession
from app.websocket.presence_service import presence_service
from app.websocket.typing_service import typing_service

@pytest.mark.asyncio
async def test_presence_service_transitions():
    user_id = str(uuid4())

    # Default offline
    p0 = presence_service.get_user_presence(user_id)
    assert p0["status"] == "offline"

    # Set online
    p1 = presence_service.set_user_presence(user_id, "online")
    assert p1["status"] == "online"

    # Update to away
    p2 = presence_service.set_user_presence(user_id, "away", custom_status="In a meeting")
    assert p2["status"] == "away"
    assert p2["custom_status"] == "In a meeting"

    # Mark offline
    p3 = presence_service.mark_user_offline(user_id)
    assert p3["status"] == "offline"

@pytest.mark.asyncio
async def test_typing_service_expiration():
    conv_id = str(uuid4())
    user_id = str(uuid4())

    # Start typing
    typing_service.start_typing(conv_id, user_id, "Alice")
    users = typing_service.get_typing_users(conv_id)
    assert len(users) == 1
    assert users[0]["user_name"] == "Alice"

    # Stop typing
    typing_service.stop_typing(conv_id, user_id)
    users_after = typing_service.get_typing_users(conv_id)
    assert len(users_after) == 0

@pytest.mark.asyncio
async def test_connection_manager_heartbeat_sweep():
    user_id = str(uuid4())
    org_id = str(uuid4())

    # Add active session
    now = datetime.utcnow()
    old_time = now - timedelta(seconds=70)

    # Test sweep logic removes expired session
    session = ConnectionSession(
        connection_id="conn_1",
        user_id=user_id,
        organization_id=org_id,
        workspace_id=None,
        websocket=None,
        connected_at=old_time,
        last_heartbeat=old_time
    )

    manager.user_sessions[user_id] = {"conn_1": session}
    assert user_id in manager.user_sessions

    # Run sweep
    await manager.sweep_stale_connections()
    assert user_id not in manager.user_sessions
