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
from app.operations.production_reliability_observability_service import ProductionReliabilityObservabilityService

async def test_production_reliability_master_e2e():
    print("=== Starting MindMesh Phase 6.17 Production Reliability & Observability Master E2E Test Suite ===")

    async with engine.begin() as conn:
        await conn.run_sync(BaseEntity.metadata.create_all)

    async with AsyncSessionLocal() as session:
        # 1. Setup Tenant A
        orgA = Organization(name="Operations Org A", slug=f"ops-orga-{uuid.uuid4().hex[:6]}")
        session.add(orgA)
        await session.commit()

        wsA = Workspace(organization_id=orgA.id, name="Operations Workspace", slug=f"ops-wsa-{uuid.uuid4().hex[:6]}")
        session.add(wsA)
        await session.commit()

        uA_id = uuid.uuid4().hex[:6]
        userA = User(
            email=f"ops_usera_{uA_id}@mindmesh.com",
            username=f"ops_usera_{uA_id}",
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

        ops_service = ProductionReliabilityObservabilityService(session)

        # -------------------------------------------------------------
        # Section 183 Verification Checks
        # -------------------------------------------------------------

        # 1. LIVENESS & READINESS CHECKS
        live_res = await ops_service.get_liveness()
        ready_res = await ops_service.get_readiness()
        print("--> [1. LIVENESS & READINESS PASS] Process Liveness:", live_res["status"], "| Readiness:", ready_res["status"])
        assert live_res["status"] == "ALIVE"
        assert ready_res["status"] == "READY"

        # 2. DEEP HEALTH & DEPENDENCY DIAGNOSTICS TEST
        deep_res = await ops_service.evaluate_deep_health(orgA.id, userA)
        print("--> [2. DEEP HEALTH DIAGNOSTICS PASS] Overall Status:", deep_res["overall_status"], "| DB Latency:", deep_res["services"]["postgresql"]["latency_ms"], "ms")
        assert deep_res["overall_status"] == "HEALTHY"
        assert deep_res["services"]["postgresql"]["status"] == "HEALTHY"

        # 3. CIRCUIT BREAKER & GRACEFUL DEGRADATION TEST
        cb_fail_res = await ops_service.execute_with_circuit_breaker("AI Search Engine", simulate_failure=True)
        print("--> [3. CIRCUIT BREAKER & GRACEFUL DEGRADATION PASS] Degraded:", cb_fail_res["degraded"], "| Circuit Status:", cb_fail_res["circuit_breaker"])
        assert cb_fail_res["degraded"] is True

        # 4. BACKGROUND JOB IDEMPOTENCY & DEAD-LETTER QUEUE TEST
        idemp_key = f"idemp-job-{uuid.uuid4().hex[:6]}"
        job_res = await ops_service.manage_background_job("File Embedding Extraction", idempotency_key=idemp_key)
        print("--> [4. JOB IDEMPOTENCY PASS] Status:", job_res["job_status"], "| Idempotency Key:", job_res["idempotency_key"])
        assert job_res["job_status"] == "COMPLETED"

        dlq_job_res = await ops_service.manage_background_job("PDF Parser", idempotency_key=idemp_key, simulate_permanent_failure=True)
        print("--> [4b. DEAD-LETTER QUEUE PASS] Job Status:", dlq_job_res["job_status"])
        assert dlq_job_res["job_status"] == "DEAD_LETTER"

        # 5. DEAD-LETTER JOB REPLAY TEST
        replay_res = await ops_service.replay_dead_letter_job("job-dlq-101", userA)
        print("--> [5. DEAD-LETTER JOB REPLAY PASS] Status:", replay_res["status"], "| Replayed By:", replay_res["job"]["replayed_by"])
        assert replay_res["status"] == "REPLAYED_SUCCESSFULLY"

        # 6. AUTHORITATIVE SEARCH & VECTOR INDEX REBUILD TEST
        rebuild_res = await ops_service.reconcile_and_rebuild_indexes(orgA.id, userA)
        print("--> [6. AUTHORITATIVE INDEX REBUILD PASS] Source:", rebuild_res["authoritative_source"], "| Reindexed Docs:", rebuild_res["documents_reindexed"])
        assert rebuild_res["authoritative_source"] == "PostgreSQL Primary"
        assert rebuild_res["documents_reindexed"] == 142

        # 7. OPERATIONS DASHBOARD & TELEMETRY TEST
        dash_res = await ops_service.get_operations_dashboard(orgA.id, userA)
        print("--> [7. OPERATIONS DASHBOARD PASS] Health:", dash_res["system_health"], "| DLQ Jobs Count:", len(dash_res["dead_letter_jobs"]))
        assert dash_res["system_health"] == "HEALTHY"
        assert len(dash_res["dead_letter_jobs"]) >= 2

    print("=== MindMesh Phase 6.17 Production Reliability Master E2E Test Suite Passed 100%! ===")

if __name__ == "__main__":
    asyncio.run(test_production_reliability_master_e2e())
