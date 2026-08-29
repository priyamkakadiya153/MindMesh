import asyncio
import sys
import os
from uuid import uuid4

sys.path.insert(0, os.path.abspath("."))

import app.models
from app.core.database import AsyncSessionLocal
from app.models.user import User
from app.models.organization import Organization
from app.workspace.models import Workspace
from app.ai.understanding import SemanticUnderstandingEngine, RequestIntent, CapabilityType
from app.ai.understanding.context_resolver import ContextResolver
from app.actions.classifier import ActionClassifier
from app.ai.orchestrator import MindMeshAIOrchestrator
from sqlalchemy import select

async def run_multi_turn_test():
    async with AsyncSessionLocal() as db:
        res_org = await db.execute(select(Organization).limit(1))
        org = res_org.scalar_one_or_none()
        if not org:
            org = Organization(id=uuid4(), name="MindMesh Verification Org", slug="verification-org")
            db.add(org)
            await db.commit()
            await db.refresh(org)

        res_ws = await db.execute(select(Workspace).where(Workspace.organization_id == org.id).limit(1))
        ws = res_ws.scalar_one_or_none()
        if not ws:
            ws = Workspace(id=uuid4(), organization_id=org.id, name="Verification Workspace", slug="verification-ws")
            db.add(ws)
            await db.commit()
            await db.refresh(ws)

        res_u = await db.execute(select(User).limit(1))
        user = res_u.scalar_one_or_none()
        if not user:
            user = User(id=uuid4(), email="admin@mindmesh.com", full_name="Admin User", current_organization_id=org.id, current_workspace_id=ws.id)
            db.add(user)
            await db.commit()
            await db.refresh(user)

        orchestrator = MindMeshAIOrchestrator(db)
        
        # Turn 1: User statement
        t1_query = "I need to review the deployment report tomorrow."
        t1_res = await orchestrator.execute(
            user_id=user.id,
            org_id=org.id,
            query=t1_query,
            workspace_id=ws.id
        )
        chat_id = t1_res.get("chat_id")
        print(f"[Turn 1 Response] Chat ID: {chat_id}")

        # Let's inspect history in DB
        from app.models.message import Message
        hist_stmt = select(Message).where(Message.chat_id == chat_id).order_by(Message.created_at.asc())
        history_msgs = (await db.execute(hist_stmt)).scalars().all()
        history = [{"role": m.role, "content": m.content} for m in history_msgs]
        print(f"[Debug History]: {history}", flush=True)

        refs = ContextResolver.resolve_references("Can you put that on my list.", history=history)
        print(f"[Debug Refs]: {refs}", flush=True)

        prop = ActionClassifier.classify("Can you put that on my list.", workspace_id=ws.id, user_id=user.id, resolved_context=refs)
        print(f"[Debug Direct Proposal]: {prop}", flush=True)

        # Turn 2: Follow-up pronoun request
        t2_query = "Can you put that on my list."
        t2_res = await orchestrator.execute(
            user_id=user.id,
            org_id=org.id,
            query=t2_query,
            conversation_id=chat_id,
            workspace_id=ws.id
        )
        print(f"[Turn 2 Response] Answer: {t2_res.get('answer')}")
        t2_prop = t2_res.get("action_proposal")
        print(f"[Turn 2 Action Proposal]: {t2_prop}")

if __name__ == "__main__":
    asyncio.run(run_multi_turn_test())
