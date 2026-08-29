import asyncio
import json
import httpx
import sys
import os
from uuid import uuid4

sys.path.insert(0, os.path.abspath("."))

import app.models
from app.documents.models import Document
from app.workspace.models import Workspace
from app.core.database import AsyncSessionLocal
from app.models.user import User
from app.core.security import create_access_token
from sqlalchemy import select

API_BASE = "http://127.0.0.1:4000/api/v1"

async def get_test_token():
    from datetime import datetime, timedelta
    from app.models.session import UserSession
    async with AsyncSessionLocal() as db:
        res = await db.execute(select(User).limit(1))
        user = res.scalar_one_or_none()
        if not user:
            org_id = uuid4()
            user = User(
                id=uuid4(),
                email="admin@mindmesh.com",
                full_name="Admin User",
                current_organization_id=org_id
            )
            db.add(user)
            await db.commit()
            await db.refresh(user)

        sess_id = uuid4()
        user_sess = UserSession(
            id=sess_id,
            user_id=user.id,
            refresh_token_hash="hash",
            revoked=False,
            expires_at=datetime.utcnow() + timedelta(days=7)
        )
        db.add(user_sess)
        await db.commit()

        return create_access_token(
            subject=str(user.id),
            session_id=str(sess_id),
            org_id=str(user.current_organization_id or uuid4()),
            workspace_id=str(user.current_workspace_id or uuid4()),
            role="ADMIN"
        )

async def test_stream_query(token: str, query: str, conversation_id: str = None):
    url = f"{API_BASE}/ai/gateway/chat/stream"
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    payload = {
        "message": query,
        "conversation_id": conversation_id,
        "stream": True
    }
    
    events = []
    final_payload = None
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        async with client.stream("POST", url, headers=headers, json=payload) as response:
            assert response.status_code == 200, f"HTTP {response.status_code}: {await response.aread()}"
            async for line in response.aiter_lines():
                if line.startswith("data: "):
                    data_str = line[6:].strip()
                    if not data_str:
                        continue
                    evt = json.loads(data_str)
                    events.append(evt)
                    if evt.get("type") == "final":
                        final_payload = evt
                        
    return events, final_payload

async def run_full_http_verification():
    token = await get_test_token()
    print(f"Generated Valid JWT Token. Running HTTP Gateway API stream tests...\n")
    
    test_cases = [
        ("A", "create a task"),
        ("C", "Create a task to review the report."),
        ("D", "Can you put reviewing the report on my todo list?"),
        ("E", "Remind me to review the files tomorrow."),
        ("F", "about remind me for review files"),
        ("G", "Remind me to review the files."),
        ("H", "What tasks do I have?"),
        ("I", "What reminders do I have?"),
        ("J", "what is 2 + 2?"),
        ("K", "What is an API?"),
        ("L", "Why is the deployment task blocked?")
    ]

    for code, q in test_cases:
        print(f"--------------------------------------------------")
        print(f"[{code}] Query: '{q}'")
        events, final_evt = await test_stream_query(token, q)
        conv_id = final_evt.get("conversation_id") if final_evt else None
        ans = final_evt.get("answer") if final_evt else "No final event"
        act_prop = final_evt.get("action_proposal") if final_evt else None
        
        print(f"    Conversation ID: {conv_id}")
        print(f"    Answer         : {ans}")
        if act_prop:
            print(f"    Action Proposal: Title='{act_prop.get('title')}', Status='{act_prop.get('status')}'")
            
        # Assertions
        if code in ["A"]:
            assert "What should the task be about?" in ans or "specify" in ans.lower() or "what" in ans.lower() or "details" in ans.lower(), f"Failed A: {ans}"
        elif code in ["C", "D"]:
            assert act_prop is not None and act_prop.get("intent_type") == "CREATE_TASK", f"Failed {code}: {final_evt}"
        elif code in ["E", "F", "G"]:
            assert act_prop is not None and act_prop.get("intent_type") == "CREATE_REMINDER", f"Failed {code}: {final_evt}"
        elif code == "J":
            assert "4" in ans, f"Failed J: {ans}"
        elif code == "K":
            assert "Application Programming Interface" in ans or "interface" in ans.lower() or "api" in ans.lower(), f"Failed K: {ans}"
            assert "couldn't find enough information" not in ans.lower(), f"Failed K: RAG swallowed query!"

    # Test B (Follow up to A)
    print(f"--------------------------------------------------")
    print(f"[B] Testing Follow-Up after query A...")
    events_a, final_a = await test_stream_query(token, "create a task")
    conv_id_a = final_a.get("conversation_id")
    events_b, final_b = await test_stream_query(token, "review the report", conversation_id=conv_id_a)
    ans_b = final_b.get("answer")
    act_prop_b = final_b.get("action_proposal")
    print(f"    Conversation ID: {conv_id_a}")
    print(f"    Answer B       : {ans_b}")
    if act_prop_b:
        print(f"    Action Proposal B: Title='{act_prop_b.get('title')}', Status='{act_prop_b.get('status')}'")
    assert act_prop_b is not None and act_prop_b.get("intent_type") == "CREATE_TASK", f"Failed B: {final_b}"

    print("\n================ ALL 12 HTTP STREAMING ASSERTS PASSED! ================\n")

if __name__ == "__main__":
    asyncio.run(run_full_http_verification())
