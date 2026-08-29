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
from app.ai.orchestrator import MindMeshAIOrchestrator
from sqlalchemy import select

async def run_fresh_clarification_test():
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
        
        # Fresh Conversation
        fresh_query = "Can you put that on my list?"
        res = await orchestrator.execute(
            user_id=user.id,
            org_id=org.id,
            query=fresh_query,
            workspace_id=ws.id
        )
        print(f"[Fresh Response] Answer: {res.get('answer')}", flush=True)
        prop = res.get("action_proposal")
        print(f"[Fresh Action Proposal]: {prop}", flush=True)

        assert "What would you like me to add to your task list?" in res.get("answer", "") or "What should the task be about?" in res.get("answer", ""), f"Unexpected response: {res.get('answer')}"
        assert prop is None or prop.get("status") == "NEEDS_CLARIFICATION", "Fresh query should prompt for clarification!"
        print("\n==========================================================================")
        print("FRESH PRONOUN CLARIFICATION TEST PASSED 100%!")
        print("==========================================================================")

if __name__ == "__main__":
    asyncio.run(run_fresh_clarification_test())
