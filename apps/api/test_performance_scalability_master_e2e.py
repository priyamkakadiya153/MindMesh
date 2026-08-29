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
from app.performance.performance_scalability_service import PerformanceScalabilityService

async def test_performance_scalability_master_e2e():
    print("=== Starting MindMesh Phase 6.18 Performance & High-Scale Architecture Master E2E Test Suite ===")

    async with engine.begin() as conn:
        await conn.run_sync(BaseEntity.metadata.create_all)

    async with AsyncSessionLocal() as session:
        # 1. Setup Tenant A
        orgA = Organization(name="High-Scale Org A", slug=f"scale-orga-{uuid.uuid4().hex[:6]}")
        session.add(orgA)
        await session.commit()

        wsA = Workspace(organization_id=orgA.id, name="High-Scale Workspace", slug=f"scale-wsa-{uuid.uuid4().hex[:6]}")
        session.add(wsA)
        await session.commit()

        uA_id = uuid.uuid4().hex[:6]
        userA = User(
            email=f"scale_usera_{uA_id}@mindmesh.com",
            username=f"scale_usera_{uA_id}",
            first_name="Priyam",
            last_name="User",
            hashed_password="mockpassword",
            phone_number=f"+1555{uA_id}",
            current_organization_id=orgA.id
        )
        session.add(userA)
        await session.commit()

        session.add(OrganizationMember(organization_id=orgA.id, user_id=userA.id, role="admin", is_active=True))
        session.add(WorkspaceMember(workspace_id=wsA.id, user_id=userA.id, role="admin", is_active=True))
        await session.commit()

        perf_service = PerformanceScalabilityService(session)

        # -------------------------------------------------------------
        # Section 205 Verification Checks
        # -------------------------------------------------------------

        # 1. P50 / P95 / P99 LATENCY BASELINES TEST
        baselines = await perf_service.get_performance_baselines(orgA.id, userA)
        print("--> [1. LATENCY BASELINES PASS] Universal Search P50:", baselines["p50_ms"]["universal_search"], "ms | P95:", baselines["p95_ms"]["universal_search"], "ms | P99:", baselines["p99_ms"]["universal_search"], "ms")
        assert baselines["p50_ms"]["universal_search"] == 18
        assert baselines["p95_ms"]["universal_search"] == 42
        assert baselines["p99_ms"]["universal_search"] == 85

        # 2. CURSOR PAGINATION & N+1 QUERY ELIMINATION TEST
        opt_res = await perf_service.optimize_query_execution("LARGE_CONVERSATION_HISTORY", None, 50)
        print("--> [2. CURSOR PAGINATION & N+1 ELIMINATION PASS] Execution Time:", opt_res["execution_time_ms"], "ms | Prevented N+1 Queries:", opt_res["n_plus_one_queries_prevented"])
        assert opt_res["execution_time_ms"] < 10.0
        assert opt_res["n_plus_one_queries_prevented"] == 48

        # 3. COST-AWARE AI MODEL ROUTING TEST
        simple_route = await perf_service.route_ai_request("SIMPLE", "Extract document metadata", userA)
        print("--> [3. SIMPLE AI ROUTING PASS] Model:", simple_route["selected_model"], "| Tokens Saved:", simple_route["tokens_saved"])
        assert simple_route["routing_path"] == "SMALL_MODEL_PATH"
        assert simple_route["tokens_saved"] == 450

        complex_route = await perf_service.route_ai_request("COMPLEX", "Multi-agent causal dependency reasoning", userA)
        print("--> [3b. DEEP REASONING ROUTING PASS] Model:", complex_route["selected_model"], "| Routing Path:", complex_route["routing_path"])
        assert complex_route["routing_path"] == "DEEP_REASONING_PATH"

        # 4. VECTOR SCOPE PARTITIONING & EMBEDDING BATCHING TEST
        doc_ids = [f"doc-{i}" for i in range(100)]
        batch_res = await perf_service.partition_and_batch_embeddings(doc_ids, orgA.id, wsA.id)
        print("--> [4. EMBEDDING BATCHING & PARTITIONING PASS] Batches:", batch_res["batches_created"], "| Scope Partition:", batch_res["scope_partition"])
        assert batch_res["batches_created"] == 10
        assert str(orgA.id) in batch_res["scope_partition"]

        # 5. TENANT FAIRNESS & WORKER CAPACITY TEST
        capacity_res = await perf_service.evaluate_worker_capacity(orgA.id)
        print("--> [5. TENANT FAIRNESS PASS] Quota Usage:", capacity_res["tenant_quota_usage"], "| Policy:", capacity_res["fairness_policy"])
        assert capacity_res["fairness_policy"] == "ROUND_ROBIN_TENANT_ISOLATED"

        # 6. CAPACITY PLANNING & LEADER ELECTION TEST
        plan_metrics = await perf_service.get_capacity_planning_metrics(orgA.id)
        print("--> [6. CAPACITY PLANNING & LEADER ELECTION PASS] Max Concurrent Users:", plan_metrics["capacity_limits"]["max_supported_concurrent_users"], "| Leader Election Lock:", plan_metrics["multi_instance_leader_election"]["coordination_mechanism"])
        assert plan_metrics["capacity_limits"]["max_supported_concurrent_users"] == 50000
        assert plan_metrics["multi_instance_leader_election"]["status"] == "ACTIVE_SINGLETON"

    print("=== MindMesh Phase 6.18 Performance & High-Scale Architecture Master E2E Test Suite Passed 100%! ===")

if __name__ == "__main__":
    asyncio.run(test_performance_scalability_master_e2e())
