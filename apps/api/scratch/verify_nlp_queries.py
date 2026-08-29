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
from app.ai.orchestrator import MindMeshAIOrchestrator
from sqlalchemy import select

async def run_nlp_verification():
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

        user_id = user.id
        org_id = org.id
        workspace_id = ws.id

        engine = SemanticUnderstandingEngine()
        orchestrator = MindMeshAIOrchestrator(db)

        test_cases = [
            # 4. Task Creation Paraphrases
            ("Create a task to review the report.", RequestIntent.CREATE_TASK, CapabilityType.ACTION_WORKFLOW),
            ("Add reviewing the report to my todo.", RequestIntent.CREATE_TASK, CapabilityType.ACTION_WORKFLOW),
            ("Put reviewing the report on my task list.", RequestIntent.CREATE_TASK, CapabilityType.ACTION_WORKFLOW),
            ("Can you add review the report as a task?", RequestIntent.CREATE_TASK, CapabilityType.ACTION_WORKFLOW),
            ("I need to review the report, add it to my tasks.", RequestIntent.CREATE_TASK, CapabilityType.ACTION_WORKFLOW),
            ("Make reviewing the report a task.", RequestIntent.CREATE_TASK, CapabilityType.ACTION_WORKFLOW),
            ("Please put review the report on my todo list.", RequestIntent.CREATE_TASK, CapabilityType.ACTION_WORKFLOW),

            # 5. Natural Reminder Language
            ("Remind me to review the files tomorrow.", RequestIntent.CREATE_REMINDER, CapabilityType.ACTION_WORKFLOW),
            ("Can you remind me tomorrow to review the files?", RequestIntent.CREATE_REMINDER, CapabilityType.ACTION_WORKFLOW),
            ("I don't want to forget to review the files tomorrow.", RequestIntent.CREATE_REMINDER, CapabilityType.ACTION_WORKFLOW),
            ("Set a reminder for reviewing the files tomorrow.", RequestIntent.CREATE_REMINDER, CapabilityType.ACTION_WORKFLOW),
            ("Remind me to review the files.", RequestIntent.CREATE_REMINDER, CapabilityType.ACTION_WORKFLOW),

            # 6. Natural DM Language
            ("Tell Dhruvil the API is ready.", RequestIntent.SEND_DIRECT_MESSAGE, CapabilityType.ACTION_WORKFLOW),
            ("Let Dhruvil know that the API integration is ready.", RequestIntent.SEND_DIRECT_MESSAGE, CapabilityType.ACTION_WORKFLOW),
            ("Send Dhruvil a message saying the API integration is ready.", RequestIntent.SEND_DIRECT_MESSAGE, CapabilityType.ACTION_WORKFLOW),
            ("Can you message Dhruvil that the API is ready?", RequestIntent.SEND_DIRECT_MESSAGE, CapabilityType.ACTION_WORKFLOW),

            # 7. Natural Automation Language
            ("Every Monday remind me to review pending tasks.", RequestIntent.CREATE_AUTOMATION, CapabilityType.ACTION_WORKFLOW),
            ("Have MindMesh remind me every Monday to review pending tasks.", RequestIntent.CREATE_AUTOMATION, CapabilityType.ACTION_WORKFLOW),
            ("I want a weekly reminder to review pending tasks.", RequestIntent.CREATE_AUTOMATION, CapabilityType.ACTION_WORKFLOW),
            ("Set up a weekly task review reminder.", RequestIntent.CREATE_AUTOMATION, CapabilityType.ACTION_WORKFLOW),

            # 8. Information vs Action Pairs
            ("What tasks do I have?", RequestIntent.TASK_QUERY, CapabilityType.TASK_SERVICE),
            ("Add reviewing the report to my tasks.", RequestIntent.CREATE_TASK, CapabilityType.ACTION_WORKFLOW),
            ("What reminders do I have?", RequestIntent.REMINDER_QUERY, CapabilityType.TASK_SERVICE),
            ("Remind me tomorrow to review the report.", RequestIntent.CREATE_REMINDER, CapabilityType.ACTION_WORKFLOW),
            ("What automations do I have?", RequestIntent.AUTOMATION_QUERY, CapabilityType.TASK_SERVICE),
            ("Remind me every Monday to review pending tasks.", RequestIntent.CREATE_AUTOMATION, CapabilityType.ACTION_WORKFLOW),
            ("What messages did I receive?", RequestIntent.DM_QUERY, CapabilityType.TASK_SERVICE),
            ("Tell Dhruvil the API is ready.", RequestIntent.SEND_DIRECT_MESSAGE, CapabilityType.ACTION_WORKFLOW),

            # 9. General Conversation
            ("hello", RequestIntent.GREETING, CapabilityType.CONVERSATIONAL_SMALLTALK),
            ("what is 2 + 2?", RequestIntent.GENERAL_KNOWLEDGE, CapabilityType.GENERAL_LLM),
            ("What is an API?", RequestIntent.GENERAL_KNOWLEDGE, CapabilityType.GENERAL_LLM),
            ("Why is the sky blue?", RequestIntent.GENERAL_KNOWLEDGE, CapabilityType.GENERAL_LLM),

            # 10. Workspace Intelligence
            ("Which tasks are pending?", RequestIntent.TASK_QUERY, CapabilityType.TASK_SERVICE),
            ("Why is the deployment task blocked?", RequestIntent.GRAPH_QUERY, CapabilityType.GRAPH_SERVICE),
            ("What did we decide about OAuth?", RequestIntent.DECISION_QUERY, CapabilityType.DECISION_SERVICE),
        ]

        passed = 0
        failed = 0

        print(f"--- Running NLP Classification Matrix ({len(test_cases)} Test Cases) ---")
        for i, (q, exp_intent, exp_cap) in enumerate(test_cases, 1):
            res = engine.parse_request(q)
            intent_ok = (res.intent == exp_intent)
            cap_ok = (res.required_capability == exp_cap)
            if intent_ok and cap_ok:
                print(f"[{i:02d}] PASS: '{q}' -> Intent={res.intent.value}, Cap={res.required_capability.value}")
                passed += 1
            else:
                print(f"[{i:02d}] FAIL: '{q}' -> Got Intent={res.intent.value} (Expected {exp_intent.value}), Cap={res.required_capability.value} (Expected {exp_cap.value})")
                failed += 1

        print(f"\n==========================================================================")
        print(f"MATRIX RESULTS: TOTAL = {len(test_cases)} | PASSED = {passed} | FAILED = {failed}")
        print(f"==========================================================================")

        assert failed == 0, f"{failed} NLP test cases failed!"

if __name__ == "__main__":
    asyncio.run(run_nlp_verification())
