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
from app.documents.models import Document
from app.projects.models import Project
from app.models.task import Task
from app.operations.autonomous_service import AutonomousKnowledgeOperationsService

async def test_autonomous_operations_e2e():
    print("=== Starting MindMesh Phase 5.2 Autonomous Knowledge Operations Master E2E Test Suite ===")

    async with engine.begin() as conn:
        await conn.run_sync(BaseEntity.metadata.create_all)

    async with AsyncSessionLocal() as session:
        # 1. Setup Tenant A
        orgA = Organization(name="Auto Ops Org A", slug=f"aop-orga-{uuid.uuid4().hex[:6]}")
        session.add(orgA)
        await session.commit()

        wsA = Workspace(organization_id=orgA.id, name="Auto Ops Workspace", slug=f"aop-wsa-{uuid.uuid4().hex[:6]}")
        session.add(wsA)
        await session.commit()

        uA_id = uuid.uuid4().hex[:6]
        userA = User(
            email=f"aop_usera_{uA_id}@mindmesh.com",
            username=f"aop_usera_{uA_id}",
            first_name="Priyam",
            last_name="User",
            hashed_password="mockpassword",
            phone_number=f"+1555{uA_id}"
        )
        session.add(userA)
        await session.commit()

        session.add(OrganizationMember(organization_id=orgA.id, user_id=userA.id, role="admin", is_active=True))
        session.add(WorkspaceMember(workspace_id=wsA.id, user_id=userA.id, role="admin", is_active=True))
        await session.commit()

        # -------------------------------------------------------------
        # Section 123 Master E2E Seeding
        # -------------------------------------------------------------
        project = Project(
            organization_id=orgA.id,
            workspace_id=wsA.id,
            name="Authentication System",
            slug=f"auth-aop-{uuid.uuid4().hex[:6]}",
            description="Autonomous operations test project"
        )
        session.add(project)
        await session.commit()

        doc1 = Document(
            organization_id=orgA.id,
            workspace_id=wsA.id,
            project_id=project.id,
            title="Authentication Architecture v1",
            filename="auth_arch_v1.md",
            original_filename="auth_arch_v1.md",
            mime_type="text/markdown",
            extension="md",
            size=1024,
            checksum_sha256="checksum_aop_1",
            storage_path="/path/aop1.md",
            uploaded_by=userA.id
        )
        doc2 = Document(
            organization_id=orgA.id,
            workspace_id=wsA.id,
            project_id=project.id,
            title="Authentication Architecture v2",
            filename="auth_arch_v2.md",
            original_filename="auth_arch_v2.md",
            mime_type="text/markdown",
            extension="md",
            size=2048,
            checksum_sha256="checksum_aop_2",
            storage_path="/path/aop2.md",
            uploaded_by=userA.id
        )
        session.add_all([doc1, doc2])
        await session.commit()

        task = Task(
            organization_id=orgA.id,
            workspace_id=wsA.id,
            project_id=project.id,
            assignee_id=userA.id,
            title="Update deployment configuration",
            description="Task to update deployment settings.",
            status="BLOCKED",
            blocked_reason="Missing production environment variable"
        )
        session.add(task)
        await session.commit()

        auto_service = AutonomousKnowledgeOperationsService(session)

        # -------------------------------------------------------------
        # Section 123 Verification Checks
        # -------------------------------------------------------------

        # 1. KNOWLEDGE OPERATIONS HEALTH OVERVIEW TEST
        hlt = await auto_service.get_operations_health(orgA.id)
        print("--> [1. OPERATIONS HEALTH PASS] Overall Status:", hlt["overall_status"], "| Freshness Monitor:", hlt["freshness_monitor"])
        assert hlt["overall_status"] == "HEALTHY"

        # 2. STALE DOCUMENT & GOVERNANCE CONFLICT DETECTION TEST
        issues_res = await auto_service.get_detected_issues_and_risks(userA, orgA.id, project.id)
        print("--> [2. DETECTED ISSUES PASS] Total Issues:", issues_res["total_issues"], "| Stale Issue Title:", issues_res["issues"][0]["title"])
        assert issues_res["total_issues"] >= 3
        assert issues_res["total_risks"] >= 1

        # 3. KNOWLEDGE DIGEST GENERATION TEST
        digest = await auto_service.get_knowledge_digest(userA, orgA.id)
        print("--> [3. KNOWLEDGE DIGEST PASS] Digest Date:", digest["digest_date"], "| Changes Count:", len(digest["important_changes"]))
        assert len(digest["important_changes"]) >= 1

        # 4. AUTOMATION RULE CREATION & TOGGLE PAUSE TEST
        rule = await auto_service.create_automation_rule(userA, orgA.id, "Decision Change Rule", "DECISION_CHANGED", "Authentication Project", "NOTIFY_USER")
        print("--> [4. AUTOMATION RULE PASS] Rule ID:", rule["rule_id"], "| Initial Enabled:", rule["is_enabled"])
        assert rule["is_enabled"] is True

        toggle_res = await auto_service.toggle_automation_rule(rule["rule_id"], False)
        print("--> [5. AUTOMATION RULE PAUSE PASS] Toggle Message:", toggle_res["message"], "| Paused Enabled State:", toggle_res["rule"]["is_enabled"])
        assert toggle_res["rule"]["is_enabled"] is False

        # 5. REPROCESS ENTITY IDEMPOTENCY TEST
        reproc_res = await auto_service.reprocess_entity(orgA.id, "DOCUMENT", doc1.id)
        print("--> [6. REPROCESS ENTITY PASS] Message:", reproc_res["message"])
        assert reproc_res["success"] is True

        # 6. MAINTENANCE REINDEX TEST
        reidx_res = await auto_service.maintenance_reindex(orgA.id)
        print("--> [7. MAINTENANCE REINDEX PASS] Message:", reidx_res["message"])
        assert reidx_res["success"] is True

    print("=== MindMesh Phase 5.2 Autonomous Knowledge Operations Master E2E Test Suite Passed 100%! ===")

if __name__ == "__main__":
    asyncio.run(test_autonomous_operations_e2e())
