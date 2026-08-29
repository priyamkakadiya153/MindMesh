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
from app.knowledge.synthesis_service import KnowledgeSynthesisEngineService

async def test_knowledge_synthesis_engine_e2e():
    print("=== Starting MindMesh Phase 4.9 Knowledge Synthesis & Organizational Memory E2E Test Suite ===")

    async with engine.begin() as conn:
        await conn.run_sync(BaseEntity.metadata.create_all)

    async with AsyncSessionLocal() as session:
        # 1. Setup Tenant A
        orgA = Organization(name="Synth Org A", slug=f"syn-orga-{uuid.uuid4().hex[:6]}")
        session.add(orgA)
        await session.commit()

        wsA = Workspace(organization_id=orgA.id, name="Synth Workspace", slug=f"syn-wsa-{uuid.uuid4().hex[:6]}")
        session.add(wsA)
        await session.commit()

        uA_id = uuid.uuid4().hex[:6]
        userA = User(
            email=f"syn_usera_{uA_id}@mindmesh.com",
            username=f"syn_usera_{uA_id}",
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
        # Section 121 Master E2E Seeding
        # -------------------------------------------------------------
        project = Project(
            organization_id=orgA.id,
            workspace_id=wsA.id,
            name="Authentication System",
            slug=f"auth-syn-{uuid.uuid4().hex[:6]}",
            description="Synthesis test project"
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
            checksum_sha256="checksum_syn_1",
            storage_path="/path/syn1.md",
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
            checksum_sha256="checksum_syn_2",
            storage_path="/path/syn2.md",
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

        synth_service = KnowledgeSynthesisEngineService(session)

        # -------------------------------------------------------------
        # Section 121 Verification Checks
        # -------------------------------------------------------------

        # 1. PROJECT SYNTHESIS TEST
        p_synth = await synth_service.synthesize(userA, orgA.id, "What is the current state of Authentication?", mode="PROJECT_STATUS", project_id=project.id)
        print("--> [1. PROJECT SYNTHESIS PASS] Mode:", p_synth["mode"], "| Current State:", p_synth["structured_answer"]["current_state"])
        assert "Authentication is in active development" in p_synth["structured_answer"]["current_state"]

        # 2. CHANGE SYNTHESIS TEST
        c_synth = await synth_service.synthesize(userA, orgA.id, "What changed with JWT?", mode="CHANGE_ANALYSIS", project_id=project.id)
        print("--> [2. CHANGE SYNTHESIS PASS] Change Answer:", c_synth["structured_answer"]["current_state"])
        assert "JWT expiry was updated" in c_synth["structured_answer"]["current_state"]

        # 3. HISTORICAL STATE SYNTHESIS TEST
        h_synth = await synth_service.synthesize(userA, orgA.id, "What was the previous JWT expiry?", mode="HISTORICAL_ANALYSIS", project_id=project.id)
        print("--> [3. HISTORICAL SYNTHESIS PASS] Historical Answer:", h_synth["structured_answer"]["current_state"])
        assert "Historical JWT expiry setting was 15 minutes" in h_synth["structured_answer"]["current_state"]

        # 4. INSUFFICIENT EVIDENCE SYNTHESIS TEST
        e_synth = await synth_service.synthesize(userA, orgA.id, "Why did the team choose 30 minutes?", mode="DECISION_ANALYSIS", project_id=project.id)
        print("--> [4. INSUFFICIENT EVIDENCE PASS] Rationale Answer:", e_synth["structured_answer"]["why"])
        assert "not a reliable source explaining the exact rationale" in e_synth["structured_answer"]["why"]

        # 5. SYNTHESIS MODES TEST
        modes = await synth_service.get_synthesis_modes()
        print("--> [5. SYNTHESIS MODES PASS] Total Supported Modes:", len(modes))
        assert len(modes) >= 7

    print("=== MindMesh Phase 4.9 Knowledge Synthesis & Organizational Memory E2E Test Suite Passed 100%! ===")

if __name__ == "__main__":
    asyncio.run(test_knowledge_synthesis_engine_e2e())
