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
from app.orchestration.memory_orchestrator_service import OrganizationalMemoryOrchestrator

async def test_memory_orchestration_master_e2e():
    print("=== Starting MindMesh Phase 6.3 Memory Orchestration Master E2E Test Suite ===")

    async with engine.begin() as conn:
        await conn.run_sync(BaseEntity.metadata.create_all)

    async with AsyncSessionLocal() as session:
        # 1. Setup Tenant A
        orgA = Organization(name="Orchestration Org A", slug=f"orc-orga-{uuid.uuid4().hex[:6]}")
        session.add(orgA)
        await session.commit()

        wsA = Workspace(organization_id=orgA.id, name="Orchestration Workspace", slug=f"orc-wsa-{uuid.uuid4().hex[:6]}")
        session.add(wsA)
        await session.commit()

        uA_id = uuid.uuid4().hex[:6]
        userA = User(
            email=f"orc_usera_{uA_id}@mindmesh.com",
            username=f"orc_usera_{uA_id}",
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
        # Section 149 Master E2E Seeding
        # -------------------------------------------------------------
        project = Project(
            organization_id=orgA.id,
            workspace_id=wsA.id,
            name="Authentication System",
            slug=f"auth-orc-{uuid.uuid4().hex[:6]}",
            description="Memory orchestration test project"
        )
        session.add(project)
        await session.commit()

        doc1 = Document(
            organization_id=orgA.id,
            workspace_id=wsA.id,
            project_id=project.id,
            title="Authentication Architecture",
            filename="auth_arch.md",
            original_filename="auth_arch.md",
            mime_type="text/markdown",
            extension="md",
            size=1024,
            checksum_sha256="checksum_orc_1",
            storage_path="/path/orc1.md",
            uploaded_by=userA.id
        )
        session.add(doc1)
        await session.commit()

        orchestrator = OrganizationalMemoryOrchestrator(session)

        # -------------------------------------------------------------
        # Section 149 Verification Checks
        # -------------------------------------------------------------

        # 1. EVENT IMPACT ANALYSIS TEST
        imp_res = await orchestrator.analyze_event_impact("DECISION_CHANGED", "dec-jwt-30m", orgA.id, userA)
        print("--> [1. IMPACT ANALYSIS PASS] Direct Impact:", len(imp_res["direct_impact"]), "| Related Impact:", len(imp_res["related_impact"]), "| Potential Impact:", len(imp_res["potential_impact"]))
        assert len(imp_res["direct_impact"]) >= 1
        assert len(imp_res["related_impact"]) >= 1

        # 2. UPSTREAM / DOWNSTREAM DEPENDENCY TEST
        dep_res = await orchestrator.get_dependency_map("task-deploy-cfg", userA)
        print("--> [2. DEPENDENCY MAP PASS] Upstream Count:", len(dep_res["upstream_dependencies"]), "| Downstream Count:", len(dep_res["downstream_impacts"]))
        assert len(dep_res["upstream_dependencies"]) >= 2
        assert len(dep_res["downstream_impacts"]) >= 2
        assert dep_res["has_circular_dependency"] is False

        # 3. KNOWLEDGE FLOW LINEAGE TEST
        flow_res = await orchestrator.get_knowledge_flow("dec-jwt-30m", userA)
        print("--> [3. KNOWLEDGE FLOW PASS] Flow Chain Steps:", len(flow_res["flow_chain"]))
        assert len(flow_res["flow_chain"]) >= 4

        # 4. KNOWLEDGE CLUSTERS TEST
        cls_res = await orchestrator.get_knowledge_clusters(orgA.id, userA)
        print("--> [4. KNOWLEDGE CLUSTERS PASS] Clusters Count:", len(cls_res), "| Concept Name:", cls_res[0]["concept_name"])
        assert len(cls_res) >= 1
        assert len(cls_res[0]["sources"]) >= 4

        # 5. ORGANIZATIONAL PATTERN DETECTION TEST
        pat_res = await orchestrator.get_organizational_patterns(orgA.id, userA)
        print("--> [5. PATTERNS PASS] Pattern Confidence:", pat_res[0]["confidence"], "| Evidence Count:", pat_res[0]["evidence_count"])
        assert len(pat_res) >= 1
        assert pat_res[0]["confidence"] == "STRONG_PATTERN"

        # 6. IMPACT SIMULATION & NON-DESTRUCTIVE ACTION TEST
        sim_res = await orchestrator.simulate_impact("JWT timeout changed to 60 minutes", "dec-jwt-30m", userA)
        print("--> [6. IMPACT SIMULATOR PASS] Simulation Only:", sim_res["simulation_only"], "| DB Modified:", sim_res["database_modified"])
        assert sim_res["simulation_only"] is True
        assert sim_res["database_modified"] is False
        assert len(sim_res["simulated_cascade"]) >= 3

        # 7. TEMPORAL MEMORY & MEMORY DIFF TEST
        diff_res = await orchestrator.compare_memory_state("Authentication Architecture", "2026-06-01", "2026-08-01", userA)
        print("--> [7. MEMORY DIFF PASS] Differences Count:", len(diff_res["differences"]))
        assert len(diff_res["differences"]) >= 1
        assert diff_res["differences"][0]["status"] == "CHANGED"

    print("=== MindMesh Phase 6.3 Memory Orchestration Master E2E Test Suite Passed 100%! ===")

if __name__ == "__main__":
    asyncio.run(test_memory_orchestration_master_e2e())
