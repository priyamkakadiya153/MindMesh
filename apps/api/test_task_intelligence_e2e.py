import asyncio
import os
import sys
import uuid
from datetime import datetime

sys.path.insert(0, os.path.abspath("."))

from app.core.database import AsyncSessionLocal, engine
from app.models.base import BaseEntity
from app.models.organization import Organization
from app.models.user import User
from app.workspace.models import Workspace, WorkspaceMember
from app.models.organization_member import OrganizationMember
from app.models.conversations import Conversation, ConversationMember, DirectMessage
from app.models.chat import Chat
from app.projects.models import Project
from app.models.task import Task
from app.models.conversation import ConversationMemory
from app.tasks.service import TaskService
from app.timeline.service import TimelineService
from app.knowledge.graph_service import KnowledgeGraphService
from app.ai.reasoner.engine import MindMeshReasoner

async def test_task_intelligence_e2e():
    print("=== Starting MindMesh Phase 3.1 Actionable Knowledge & Task Intelligence E2E Test Suite ===")

    async with engine.begin() as conn:
        await conn.run_sync(BaseEntity.metadata.create_all)
        from sqlalchemy import text
        await conn.execute(text("ALTER TABLE tasks ADD COLUMN IF NOT EXISTS title VARCHAR;"))
        await conn.execute(text("ALTER TABLE tasks ADD COLUMN IF NOT EXISTS task_type VARCHAR DEFAULT 'TASK';"))
        await conn.execute(text("ALTER TABLE tasks ADD COLUMN IF NOT EXISTS priority VARCHAR DEFAULT 'MEDIUM';"))
        await conn.execute(text("ALTER TABLE tasks ADD COLUMN IF NOT EXISTS workspace_id UUID;"))
        await conn.execute(text("ALTER TABLE tasks ADD COLUMN IF NOT EXISTS source_type VARCHAR;"))
        await conn.execute(text("ALTER TABLE tasks ADD COLUMN IF NOT EXISTS source_id UUID;"))
        await conn.execute(text("ALTER TABLE tasks ADD COLUMN IF NOT EXISTS decision_id UUID;"))
        await conn.execute(text("ALTER TABLE tasks ADD COLUMN IF NOT EXISTS conversation_id UUID;"))
        await conn.execute(text("ALTER TABLE tasks ADD COLUMN IF NOT EXISTS message_id UUID;"))
        await conn.execute(text("ALTER TABLE tasks ADD COLUMN IF NOT EXISTS document_id UUID;"))
        await conn.execute(text("ALTER TABLE tasks ADD COLUMN IF NOT EXISTS completed_at TIMESTAMP WITHOUT TIME ZONE;"))
        await conn.execute(text("ALTER TABLE tasks ADD COLUMN IF NOT EXISTS completed_by UUID;"))
        await conn.execute(text("ALTER TABLE tasks ADD COLUMN IF NOT EXISTS is_ai_extracted BOOLEAN DEFAULT FALSE;"))
        await conn.execute(text("ALTER TABLE tasks ADD COLUMN IF NOT EXISTS blocked_reason VARCHAR;"))

    async with AsyncSessionLocal() as session:
        # 1. Setup Tenant A
        orgA = Organization(name="Task Org A", slug=f"task-orga-{uuid.uuid4().hex[:6]}")
        session.add(orgA)
        await session.commit()

        wsA = Workspace(organization_id=orgA.id, name="Engineering WS", slug=f"task-wsa-{uuid.uuid4().hex[:6]}")
        session.add(wsA)
        await session.commit()

        uA_id = uuid.uuid4().hex[:6]
        userA = User(
            email=f"task_usera_{uA_id}@mindmesh.com",
            username=f"task_usera_{uA_id}",
            first_name="Priyam",
            last_name="User",
            hashed_password="mockpassword",
            phone_number=f"+1555{uA_id}"
        )
        session.add(userA)

        uB_id = uuid.uuid4().hex[:6]
        userB = User(
            email=f"task_userb_{uB_id}@mindmesh.com",
            username=f"task_userb_{uB_id}",
            first_name="User",
            last_name="B",
            hashed_password="mockpassword",
            phone_number=f"+1555{uB_id}"
        )
        session.add(userB)
        await session.commit()

        session.add(OrganizationMember(organization_id=orgA.id, user_id=userA.id, role="admin", is_active=True))
        session.add(OrganizationMember(organization_id=orgA.id, user_id=userB.id, role="member", is_active=True))
        session.add(WorkspaceMember(workspace_id=wsA.id, user_id=userA.id, role="admin", is_active=True))
        session.add(WorkspaceMember(workspace_id=wsA.id, user_id=userB.id, role="member", is_active=True))
        await session.commit()

        # 2. Setup Tenant B (Unrelated Org)
        orgB = Organization(name="Task Org B", slug=f"task-orgb-{uuid.uuid4().hex[:6]}")
        session.add(orgB)
        await session.commit()

        wsB = Workspace(organization_id=orgB.id, name="Org B WS", slug=f"task-wsb-{uuid.uuid4().hex[:6]}")
        session.add(wsB)
        await session.commit()

        uC_id = uuid.uuid4().hex[:6]
        userC = User(
            email=f"task_userc_{uC_id}@mindmesh.com",
            username=f"task_userc_{uC_id}",
            first_name="User",
            last_name="C",
            hashed_password="mockpassword",
            phone_number=f"+1555{uC_id}"
        )
        session.add(userC)
        await session.commit()

        session.add(OrganizationMember(organization_id=orgB.id, user_id=userC.id, role="admin", is_active=True))
        session.add(WorkspaceMember(workspace_id=wsB.id, user_id=userC.id, role="admin", is_active=True))
        await session.commit()

        # -------------------------------------------------------------
        # Section 78 Required Master E2E Seeding
        # -------------------------------------------------------------
        project = Project(
            organization_id=orgA.id,
            workspace_id=wsA.id,
            name="Authentication System",
            slug=f"auth-sys-{uuid.uuid4().hex[:6]}",
            description="Core authentication project"
        )
        session.add(project)
        await session.commit()

        chat = Chat(
            organization_id=orgA.id,
            workspace_id=wsA.id,
            user_id=userA.id,
            title="Architecture Discussion"
        )
        session.add(chat)
        await session.commit()

        conv_mem = ConversationMemory(
            chat_id=chat.id,
            organization_id=orgA.id,
            workspace_id=wsA.id,
            project_id=project.id,
            memory_type="decision",
            content="PostgreSQL selected for production",
            importance=5
        )
        session.add(conv_mem)
        await session.commit()

        conv = Conversation(
            organization_id=orgA.id,
            workspace_id=wsA.id,
            project_id=project.id,
            type="group",
            name="Architecture Team",
            visibility="private"
        )
        session.add(conv)
        await session.commit()

        session.add(ConversationMember(conversation_id=conv.id, user_id=userA.id, role="admin"))
        session.add(ConversationMember(conversation_id=conv.id, user_id=userB.id, role="member"))
        await session.commit()

        msg1 = DirectMessage(
            conversation_id=conv.id,
            sender_id=userA.id,
            organization_id=orgA.id,
            workspace_id=wsA.id,
            content="PostgreSQL should be our production database."
        )
        msg2 = DirectMessage(
            conversation_id=conv.id,
            sender_id=userB.id,
            organization_id=orgA.id,
            workspace_id=wsA.id,
            content="Agreed."
        )
        msg3 = DirectMessage(
            conversation_id=conv.id,
            sender_id=userA.id,
            organization_id=orgA.id,
            workspace_id=wsA.id,
            content="Priyam, please update the deployment configuration by Friday."
        )
        session.add(msg1)
        session.add(msg2)
        session.add(msg3)
        await session.commit()

        # Instantiate TaskService
        task_service = TaskService(session)

        # Parse relative deadline
        due_dt = task_service.parse_relative_deadline("Friday")

        # Create AI-extracted task
        task = await task_service.create_task(
            organization_id=orgA.id,
            workspace_id=wsA.id,
            project_id=project.id,
            title="Update deployment configuration",
            description="Update deployment configuration by Friday following PostgreSQL production decision.",
            assignee_id=userA.id,
            due_date=due_dt,
            priority="HIGH",
            task_type="ACTION_ITEM",
            source_type="CONVERSATION",
            source_id=conv.id,
            decision_id=conv_mem.id,
            conversation_id=conv.id,
            message_id=msg3.id,
            is_ai_extracted=True
        )

        # -------------------------------------------------------------
        # Section 78 Master Verification Checks
        # -------------------------------------------------------------

        # 1. TASK LIST TEST
        all_tasks = await task_service.list_tasks(userA.id, orgA.id, wsA.id)
        print("--> [1. TASK LIST PASS] Count:", len(all_tasks))
        assert len(all_tasks) >= 1
        assert all_tasks[0].title == "Update deployment configuration"

        # 2. TASK DETAIL & PROVENANCE TEST
        assert all_tasks[0].assignee_id == userA.id
        assert all_tasks[0].is_ai_extracted is True
        assert all_tasks[0].decision_id == conv_mem.id

        # 3. WHY PROVENANCE TEST
        why_res = await task_service.get_task_provenance_explanation(task.id, orgA.id, userA.id)
        print("--> [3. WHY PROVENANCE PASS]", why_res["provenance_summary"])
        assert "PostgreSQL selected for production" in why_res["provenance_summary"] or len(why_res["citations"]) > 0

        # 4. SOURCE LINK TEST
        assert str(all_tasks[0].conversation_id) == str(conv.id)

        # 5. GRAPH TEST
        kg_service = KnowledgeGraphService(session)
        search_n = await kg_service.search_nodes(userA, orgA.id, "deployment", workspace_id=wsA.id)
        print("--> [5. GRAPH NODES PASS] Count:", len(search_n))
        assert len(search_n) >= 1

        # 6. TIMELINE TEST
        tl_service = TimelineService(session)
        events_res = await tl_service.get_timeline_events(userA, orgA.id, workspace_id=wsA.id)
        events = events_res.get("events", [])
        print("--> [6. TIMELINE EVENTS PASS] Count:", len(events))
        assert len(events) >= 1

        # 7. ASK MINDSMESH REASONING TEST
        reasoner = MindMeshReasoner(session)
        ai_ans = await reasoner.reason_and_answer(userA.id, orgA.id, "Why do I have the deployment configuration task?", wsA.id)
        print("--> [8. ASK MINDSMESH TASK CONTEXT PASS] Answer:", ai_ans["answer"])
        assert len(ai_ans["answer"]) > 0

        # 8. COMPLETE TASK TEST
        updated_task = await task_service.update_task_status(
            task_id=task.id,
            organization_id=orgA.id,
            new_status="COMPLETED",
            user_id=userA.id,
            completion_note="Deployment config updated and deployed to production cluster."
        )
        print("--> [9. TASK COMPLETE PASS] New status:", updated_task.status)
        assert updated_task.status == "COMPLETED"
        assert updated_task.completed_at is not None

        # 9. SECURITY ISOLATION TEST (User C from Org B)
        c_tasks = await task_service.list_tasks(userC.id, orgB.id, wsB.id)
        print("--> [10. SECURITY PASS] Org B task count:", len(c_tasks))
        assert len(c_tasks) == 0

    print("=== MindMesh Phase 3.1 Actionable Knowledge & Task Intelligence E2E Test Suite Passed 100%! ===")

if __name__ == "__main__":
    asyncio.run(test_task_intelligence_e2e())
