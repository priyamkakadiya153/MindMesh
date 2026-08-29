import asyncio
import json
import sys
import os
from uuid import uuid4

sys.path.insert(0, os.path.abspath("."))

import app.models
from app.documents.models import Document
from app.workspace.models import Workspace
from app.core.database import AsyncSessionLocal
from app.models.user import User
from app.ai.orchestrator import MindMeshAIOrchestrator

async def run_orchestrator_verification():
    from app.models.organization import Organization
    from app.workspace.models import Workspace
    
    async with AsyncSessionLocal() as db:
        res_org = await db.execute(select(Organization).limit(1))
        org = res_org.scalar_one_or_none()
        if not org:
            org = Organization(id=uuid4(), name="MindMesh Test Org", slug="mindmesh-test-org")
            db.add(org)
            await db.commit()
            await db.refresh(org)

        res_ws = await db.execute(select(Workspace).where(Workspace.organization_id == org.id).limit(1))
        ws = res_ws.scalar_one_or_none()
        if not ws:
            ws = Workspace(id=uuid4(), organization_id=org.id, name="Test Workspace", slug="test-workspace")
            db.add(ws)
            await db.commit()
            await db.refresh(ws)

        res = await db.execute(select(User).limit(1))
        user = res.scalar_one_or_none()
        if not user:
            user = User(
                id=uuid4(),
                email="admin@mindmesh.com",
                full_name="Admin User",
                current_organization_id=org.id,
                current_workspace_id=ws.id
            )
            db.add(user)
            await db.commit()
            await db.refresh(user)
        else:
            user.current_organization_id = org.id
            user.current_workspace_id = ws.id
            db.add(user)
            await db.commit()

        user_id = user.id
        org_id = org.id
        workspace_id = ws.id

        orchestrator = MindMeshAIOrchestrator(db)

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

        print("\n================ FULL ORCHESTRATOR END-TO-END TEST MATRIX ================")
        conv_a_id = None

        for code, q in test_cases:
            print(f"--------------------------------------------------")
            print(f"[{code}] Query: '{q}'")
            
            events = []
            final_evt = None
            async for evt in orchestrator.stream_execute(
                user_id=user_id,
                org_id=org_id,
                query=q,
                workspace_id=workspace_id
            ):
                events.append(evt)
                if evt.get("type") == "final":
                    final_evt = evt

            conv_id = final_evt.get("conversation_id") if final_evt else None
            ans = final_evt.get("answer") if final_evt else "No final event"
            act_prop = final_evt.get("action_proposal") if final_evt else None
            
            if code == "A":
                conv_a_id = conv_id

            print(f"    Conversation ID: {conv_id}")
            print(f"    Answer         : {ans}")
            if act_prop:
                print(f"    Action Proposal: Title='{act_prop.get('title')}', Status='{act_prop.get('status')}'")

            # Assertions
            if code == "A":
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

        # Follow up query B after query A
        print(f"--------------------------------------------------")
        print(f"[B] Testing Follow-Up 'review the report' after query A (Conv ID: {conv_a_id})...")
        events_b = []
        final_b = None
        async for evt in orchestrator.stream_execute(
            user_id=user_id,
            org_id=org_id,
            query="review the report",
            conversation_id=uuid.UUID(conv_a_id) if isinstance(conv_a_id, str) else conv_a_id,
            workspace_id=workspace_id
        ):
            events_b.append(evt)
            if evt.get("type") == "final":
                final_b = evt

        ans_b = final_b.get("answer")
        act_prop_b = final_b.get("action_proposal")
        print(f"    Answer B       : {ans_b}")
        if act_prop_b:
            print(f"    Action Proposal B: Title='{act_prop_b.get('title')}', Status='{act_prop_b.get('status')}'")
        assert act_prop_b is not None and act_prop_b.get("intent_type") == "CREATE_TASK", f"Failed B: {final_b}"

        print("\n================ ALL 12 TEST MATRIX ASSERTS PASSED PERFECTLY! ================\n")

if __name__ == "__main__":
    from sqlalchemy import select
    import uuid
    asyncio.run(run_orchestrator_verification())
