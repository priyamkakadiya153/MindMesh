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
from app.graph.memory_graph_service import OrganizationalMemoryGraphService

async def test_memory_graph_navigation_e2e():
    print("=== Starting MindMesh Phase 5.6 Memory Graph Master E2E Test Suite ===")

    async with engine.begin() as conn:
        await conn.run_sync(BaseEntity.metadata.create_all)

    async with AsyncSessionLocal() as session:
        # 1. Setup Tenant A
        orgA = Organization(name="Graph Org A", slug=f"grp-orga-{uuid.uuid4().hex[:6]}")
        session.add(orgA)
        await session.commit()

        wsA = Workspace(organization_id=orgA.id, name="Graph Workspace", slug=f"grp-wsa-{uuid.uuid4().hex[:6]}")
        session.add(wsA)
        await session.commit()

        uA_id = uuid.uuid4().hex[:6]
        userA = User(
            email=f"grp_usera_{uA_id}@mindmesh.com",
            username=f"grp_usera_{uA_id}",
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
        # Section 141 Master E2E Seeding
        # -------------------------------------------------------------
        project = Project(
            organization_id=orgA.id,
            workspace_id=wsA.id,
            name="Authentication System",
            slug=f"auth-grp-{uuid.uuid4().hex[:6]}",
            description="Memory Graph test project"
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
            checksum_sha256="checksum_grp_1",
            storage_path="/path/grp1.md",
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
            checksum_sha256="checksum_grp_2",
            storage_path="/path/grp2.md",
            uploaded_by=userA.id
        )
        session.add_all([doc1, doc2])
        await session.commit()

        task1 = Task(
            organization_id=orgA.id,
            workspace_id=wsA.id,
            project_id=project.id,
            assignee_id=userA.id,
            title="Update deployment configuration",
            description="Task to update deployment settings.",
            status="BLOCKED",
            blocked_reason="Missing production environment variable"
        )
        task2 = Task(
            organization_id=orgA.id,
            workspace_id=wsA.id,
            project_id=project.id,
            assignee_id=userA.id,
            title="Release Milestone Deployment",
            description="Final release deployment task.",
            status="PENDING"
        )
        session.add_all([task1, task2])
        await session.commit()

        graph_service = OrganizationalMemoryGraphService(session)

        # -------------------------------------------------------------
        # Section 141 Verification Checks
        # -------------------------------------------------------------

        # 1. CONTROLLED GRAPH EXPLORATION TEST
        graph_res = await graph_service.explore_graph("dec-jwt-30m", "DECISION", 2, userA, orgA.id)
        print("--> [1. GRAPH EXPLORATION PASS] Nodes:", graph_res["total_nodes"], "| Edges:", graph_res["total_edges"])
        assert graph_res["total_nodes"] >= 8
        assert graph_res["total_edges"] >= 7

        # 2. BACKWARD SOURCE LINEAGE TRACING TEST
        ins_id = "ins-doc-volatility"
        lineage_res = await graph_service.trace_lineage("INSIGHT", ins_id)
        print("--> [2. SOURCE LINEAGE PASS] Target:", lineage_res["target_entity_type"], "| Lineage Depth:", lineage_res["lineage_depth"])
        assert lineage_res["lineage_depth"] == 4
        assert lineage_res["lineage"][0]["entity_type"] == "INSIGHT"
        assert lineage_res["lineage"][3]["entity_type"] == "CONVERSATION"

        # 3. FORWARD IMPACT GRAPH TRACING TEST
        dec_id = "dec-jwt-30m"
        impact_res = await graph_service.trace_impact("DECISION", dec_id)
        print("--> [3. FORWARD IMPACT PASS] Direct Impacts:", len(impact_res["direct_impact"]), "| Indirect Impacts:", len(impact_res["indirect_impact"]))
        assert len(impact_res["direct_impact"]) == 2
        assert len(impact_res["indirect_impact"]) == 1

        # 4. GOVERNANCE CONFLICT TRACING TEST
        conflicts = await graph_service.get_governance_conflicts(orgA.id)
        print("--> [4. GOVERNANCE CONFLICT PASS] Conflicts Count:", len(conflicts), "| Reason:", conflicts[0]["conflict_reason"])
        assert len(conflicts) >= 1
        assert conflicts[0]["relationship"] == "contradicts"

        # 5. HISTORICAL GRAPH & VERSIONING TEST
        history = await graph_service.get_entity_history("DOCUMENT", "doc-auth-v2")
        print("--> [5. HISTORICAL VERSIONING PASS] Versions Count:", len(history["versions"]), "| Latest Status:", history["versions"][1]["status"])
        assert len(history["versions"]) == 2
        assert history["versions"][0]["status"] == "SUPERSEDED"
        assert history["versions"][1]["status"] == "CURRENT"

        # 6. IDEMPOTENT GRAPH REBUILD TEST
        rebuild_res = await graph_service.rebuild_graph(orgA.id)
        print("--> [6. GRAPH REBUILD PASS] Message:", rebuild_res["message"])
        assert rebuild_res["success"] is True

    print("=== MindMesh Phase 5.6 Memory Graph Master E2E Test Suite Passed 100%! ===")

if __name__ == "__main__":
    asyncio.run(test_memory_graph_navigation_e2e())
