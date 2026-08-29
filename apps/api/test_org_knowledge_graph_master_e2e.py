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
from app.graph.organizational_knowledge_graph_service import OrganizationalKnowledgeGraphService

async def test_org_knowledge_graph_master_e2e():
    print("=== Starting MindMesh Phase 6.9 Organizational Knowledge Graph Master E2E Test Suite ===")

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
        # Section 172 Master E2E Seeding
        # -------------------------------------------------------------
        project = Project(
            organization_id=orgA.id,
            workspace_id=wsA.id,
            name="Authentication Migration",
            slug=f"auth-grp-{uuid.uuid4().hex[:6]}",
            description="Causal graph test project"
        )
        session.add(project)
        await session.commit()

        graph_service = OrganizationalKnowledgeGraphService(session)

        # -------------------------------------------------------------
        # Section 172 Verification Checks
        # -------------------------------------------------------------

        # 1. SUBGRAPH TRAVERSAL TEST
        sg_res = await graph_service.get_graph_subgraph(project.id, userA)
        print("--> [1. SUBGRAPH TRAVERSAL PASS] Nodes:", sg_res["nodes_count"], "| Edges:", sg_res["edges_count"])
        assert sg_res["nodes_count"] >= 5
        assert sg_res["edges_count"] >= 4

        # 2. EXPLAINABLE PATH FINDING TEST
        path_res = await graph_service.find_explainable_path("node-dec-101", "node-out-101", userA)
        print("--> [2. EXPLAINABLE PATH PASS] Path Steps:", path_res["path_length"], "| Explanation:", path_res["explanation"])
        assert path_res["path_length"] >= 5
        assert path_res["is_causal"] is True

        # 3. NON-DESTRUCTIVE CHANGE SIMULATION TEST
        sim_res = await graph_service.simulate_change_impact("node-dec-101", userA)
        print("--> [3. IMPACT SIMULATION PASS] Direct:", sim_res["blast_radius_summary"]["direct_impact_count"], "| Mode:", sim_res["simulation_mode"])
        assert sim_res["blast_radius_summary"]["direct_impact_count"] == 2

        # 4. SYSTEMIC ROOT-CAUSE ANALYSIS TEST
        rc_res = await graph_service.perform_root_cause_analysis("inc-809", userA)
        print("--> [4. ROOT CAUSE ANALYSIS PASS] Primary Cause:", rc_res["root_cause_tree"]["primary_candidate"], "| Focus:", rc_res["systemic_focus"])
        assert "Session Pooling" in rc_res["root_cause_tree"]["primary_candidate"]

        # 5. BOTTLENECK & KNOWLEDGE FRAGILITY TEST
        bot_res = await graph_service.detect_system_bottlenecks(orgA.id, userA)
        print("--> [5. BOTTLENECKS PASS] Total Bottlenecks:", len(bot_res), "| Type:", bot_res[0]["type"])
        assert len(bot_res) >= 2
        assert bot_res[0]["type"] == "KNOWLEDGE_FRAGILITY"

        # 6. GRAPH DIGEST TEST
        dig_res = await graph_service.get_graph_digest(orgA.id, userA)
        print("--> [6. GRAPH DIGEST PASS] Total Nodes:", dig_res["total_nodes"], "| Causal Chains:", dig_res["causal_chains_tracked"])
        assert dig_res["total_nodes"] >= 40

    print("=== MindMesh Phase 6.9 Organizational Knowledge Graph Master E2E Test Suite Passed 100%! ===")

if __name__ == "__main__":
    asyncio.run(test_org_knowledge_graph_master_e2e())
