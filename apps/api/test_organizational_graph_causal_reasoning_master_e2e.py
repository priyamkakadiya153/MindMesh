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
from app.graph.organizational_graph_causal_reasoning_service import OrganizationalGraphCausalReasoningService

async def test_organizational_graph_causal_reasoning_master_e2e():
    print("=== Starting MindMesh Phase 6.24 Organizational Graph Intelligence Master E2E Test Suite ===")

    async with engine.begin() as conn:
        await conn.run_sync(BaseEntity.metadata.create_all)

    async with AsyncSessionLocal() as session:
        # 1. Setup Tenant & Auth
        org = Organization(name="Graph Org", slug=f"graph-org-{uuid.uuid4().hex[:6]}")
        session.add(org)
        await session.commit()

        ws = Workspace(organization_id=org.id, name="Graph Workspace", slug=f"graph-ws-{uuid.uuid4().hex[:6]}")
        session.add(ws)
        await session.commit()

        u_id = uuid.uuid4().hex[:6]
        user = User(
            email=f"graph_user_{u_id}@mindmesh.com",
            username=f"graph_user_{u_id}",
            first_name="Priyam",
            last_name="User",
            hashed_password="mockpassword",
            phone_number=f"+1555{u_id}",
            current_organization_id=org.id
        )
        session.add(user)
        await session.commit()

        session.add(OrganizationMember(organization_id=org.id, user_id=user.id, role="admin", is_active=True))
        session.add(WorkspaceMember(workspace_id=ws.id, user_id=user.id, role="admin", is_active=True))
        await session.commit()

        graph_service = OrganizationalGraphCausalReasoningService(session)

        # -------------------------------------------------------------
        # Section 175 Verification Checks
        # -------------------------------------------------------------

        # 1. MULTI-HOP GRAPH TRAVERSAL & SUBGRAPH QUERY TEST
        subgraph = await graph_service.query_organizational_graph(
            center_node_id="proj-601",
            max_depth=2,
            organization_id=org.id,
            user=user
        )
        print("--> [1. SUBGRAPH TRAVERSAL PASS] Nodes Count:", subgraph["subgraph"]["total_nodes"], "| Edges Count:", subgraph["subgraph"]["total_edges"])
        assert subgraph["subgraph"]["total_nodes"] == 6
        assert subgraph["subgraph"]["total_edges"] == 5

        # 2. DERIVATION LINEAGE TRACEABILITY TEST
        lineage = await graph_service.trace_knowledge_and_decision_lineage("dec-301", "BACKWARD", org.id, user)
        print("--> [2. DERIVATION LINEAGE PASS] Path Length:", len(lineage["lineage_path"]), "| Explanation:", lineage["explanation"])
        assert len(lineage["lineage_path"]) == 4
        assert lineage["lineage_path"][0]["node_type"] == "DOCUMENT"

        # 3. BLAST RADIUS & CHANGE PROPAGATION IMPACT TEST
        impact = await graph_service.analyze_change_impact_and_blast_radius("serv-501", "Refactor Auth Microservice DB", org.id, user)
        print("--> [3. BLAST RADIUS PASS] Classification:", impact["blast_radius_classification"], "| Impact Score:", impact["impact_score"], "| Direct Impact:", len(impact["affected_objects"]["direct"]))
        assert impact["blast_radius_classification"] == "LARGE"
        assert impact["impact_score"] == 82

        # 4. ROOT CAUSE ANALYSIS & CAUSAL HYPOTHESIS TEST
        root_cause = await graph_service.perform_root_cause_analysis("Release Milestone v2.4 is delayed", org.id, user)
        hyp = root_cause["causal_hypotheses"][0]
        print("--> [4. ROOT CAUSE ANALYSIS PASS] Classification:", hyp["causal_classification"], "| Cause:", hyp["proposed_cause"], "| Effect:", hyp["target_effect"])
        assert hyp["causal_classification"] == "POTENTIALLY_CAUSAL"
        assert root_cause["verified_causality_established"] is False

        # 5. SYSTEMIC BOTTLENECK & BUS FACTOR TEST
        bottlenecks = await graph_service.detect_systemic_bottlenecks_and_risks(org.id, user)
        print("--> [5. SYSTEMIC BOTTLENECKS PASS] Bottlenecks Count:", len(bottlenecks["systemic_bottlenecks"]), "| Bus Factor Warning:", bottlenecks["systemic_bottlenecks"][1]["bus_factor_warning"])
        assert len(bottlenecks["systemic_bottlenecks"]) == 2
        assert bottlenecks["systemic_bottlenecks"][1]["bus_factor_warning"] is True

    print("=== MindMesh Phase 6.24 Organizational Graph Intelligence Master E2E Test Suite Passed 100%! ===")

if __name__ == "__main__":
    asyncio.run(test_organizational_graph_causal_reasoning_master_e2e())
