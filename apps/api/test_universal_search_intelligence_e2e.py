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
from app.models.chat import Chat
from app.models.message import Message
from app.projects.models import Project
from app.models.task import Task
from app.models.conversation import ConversationMemory
from app.models.search import SearchIndex
from app.documents.service import DocumentService
from app.processing.pipeline import ProcessingPipeline
from app.search.universal_service import UniversalSearchIntelligenceService

async def test_universal_search_intelligence_e2e():
    print("=== Starting MindMesh Phase 4.2 Universal Knowledge Search E2E Test Suite ===")

    async with engine.begin() as conn:
        await conn.run_sync(BaseEntity.metadata.create_all)

    async with AsyncSessionLocal() as session:
        # 1. Setup Tenant A
        orgA = Organization(name="Search Org A", slug=f"srch-orga-{uuid.uuid4().hex[:6]}")
        session.add(orgA)
        await session.commit()

        wsA = Workspace(organization_id=orgA.id, name="Search Workspace", slug=f"srch-wsa-{uuid.uuid4().hex[:6]}")
        session.add(wsA)
        await session.commit()

        uA_id = uuid.uuid4().hex[:6]
        userA = User(
            email=f"srch_usera_{uA_id}@mindmesh.com",
            username=f"srch_usera_{uA_id}",
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

        # 2. Setup Tenant B (Unrelated Org)
        orgB = Organization(name="Search Org B", slug=f"srch-orgb-{uuid.uuid4().hex[:6]}")
        session.add(orgB)
        await session.commit()

        wsB = Workspace(organization_id=orgB.id, name="Org B WS", slug=f"srch-wsb-{uuid.uuid4().hex[:6]}")
        session.add(wsB)
        await session.commit()

        uC_id = uuid.uuid4().hex[:6]
        userC = User(
            email=f"srch_userc_{uC_id}@mindmesh.com",
            username=f"srch_userc_{uC_id}",
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
        # Section 121 Master E2E Seeding
        # -------------------------------------------------------------
        project = Project(
            organization_id=orgA.id,
            workspace_id=wsA.id,
            name="Authentication System",
            slug=f"auth-srch-{uuid.uuid4().hex[:6]}",
            description="Core authentication search project"
        )
        session.add(project)
        await session.commit()

        doc_service = DocumentService(session)
        doc1 = await doc_service.upload_document(
            file_content=b"Authentication Architecture Specification\n\nJSON Web Token (JWT) configuration details.",
            filename="auth_arch.txt",
            content_type="text/plain",
            org_id=orgA.id,
            workspace_id=wsA.id,
            user_id=userA.id,
            title="Authentication Architecture",
            visibility="private"
        )
        doc1.project_id = project.id

        dst_file = await doc_service.upload_document(
            file_content=b"Specialized DST File Content",
            filename="authentication-design.dst",
            content_type="application/octet-stream",
            org_id=orgA.id,
            workspace_id=wsA.id,
            user_id=userA.id,
            title="authentication-design.dst",
            visibility="private"
        )
        dst_file.project_id = project.id
        await session.commit()

        proc_job = ProcessingPipeline(session)
        await proc_job.process_document(doc1.id)
        await proc_job.process_document(dst_file.id)

        # Seed Search Index entries for Decision, Task, Message
        idx1 = SearchIndex(
            organization_id=orgA.id,
            workspace_id=wsA.id,
            entity_type="decision",
            entity_id=uuid.uuid4(),
            title="JWT expiry set to 30 minutes",
            content="We agreed on 30-minute JWT token expiry for production security.",
            metadata_json={"governance_status": "Current"}
        )
        idx2 = SearchIndex(
            organization_id=orgA.id,
            workspace_id=wsA.id,
            entity_type="decision",
            entity_id=uuid.uuid4(),
            title="Old JWT 15-minute expiry decision",
            content="Historical decision: 15-minute token expiry.",
            metadata_json={"governance_status": "SUPERSEDED"}
        )
        idx3 = SearchIndex(
            organization_id=orgA.id,
            workspace_id=wsA.id,
            entity_type="task",
            entity_id=uuid.uuid4(),
            title="Update deployment configuration",
            content="Task to update production authentication deployment configuration."
        )
        session.add_all([idx1, idx2, idx3])
        await session.commit()

        search_service = UniversalSearchIntelligenceService(session)

        # -------------------------------------------------------------
        # Section 121 Verification Checks
        # -------------------------------------------------------------

        # 1. MULTI-ENTITY UNIVERSAL SEARCH TEST
        res_univ = await search_service.execute_hybrid_search("authentication", userA, orgA.id, wsA.id, project.id)
        print("--> [1. UNIVERSAL SEARCH PASS] Total Results:", res_univ["total_results"], "| Intent:", res_univ["intent"])
        assert res_univ["total_results"] >= 2

        # 2. SEMANTIC & CONCEPT EXPANSION TEST (JWT -> JSON Web Token)
        res_jwt = await search_service.execute_hybrid_search("JWT settings", userA, orgA.id, wsA.id, project.id)
        print("--> [2. CONCEPT EXPANSION PASS] Results Count:", res_jwt["total_results"])
        assert res_jwt["total_results"] >= 1

        # 3. NATURAL LANGUAGE QUESTION SEARCH TEST
        res_q = await search_service.execute_hybrid_search("What was decided about JWT expiry?", userA, orgA.id, wsA.id, project.id)
        print("--> [3. QUESTION SEARCH PASS] Parsed Intent:", res_q["intent"], "| Target Entity:", res_q.get("target_entity"))
        assert res_q["intent"] == "QUESTION"

        # 4. SPECIALIZED FILE SEARCH TEST
        res_dst = await search_service.execute_hybrid_search("authentication-design.dst", userA, orgA.id, wsA.id, project.id)
        print("--> [4. SPECIALIZED FILE PASS] DST File Result Title:", res_dst["results"][0]["title"])
        assert "authentication-design.dst" in res_dst["results"][0]["title"]

        # 5. HISTORICAL SUPERSEDED DECISION TEST
        res_old = await search_service.execute_hybrid_search("Old JWT 15-minute", userA, orgA.id, wsA.id, project.id)
        old_item = next(r for r in res_old["results"] if "Old JWT" in r["title"])
        print("--> [5. HISTORICAL DECISION PASS] Governance Status:", old_item["governance_status"])
        assert old_item["governance_status"] == "SUPERSEDED"

        # 6. SECURITY & PERMISSION ISOLATION TEST (User C in Org B)
        res_orgB = await search_service.execute_hybrid_search("authentication", userC, orgB.id, wsB.id)
        print("--> [6. SECURITY PASS] Org B Results Returned:", res_orgB["total_results"])
        assert res_orgB["total_results"] == 0

    print("=== MindMesh Phase 4.2 Universal Knowledge Search E2E Test Suite Passed 100%! ===")

if __name__ == "__main__":
    asyncio.run(test_universal_search_intelligence_e2e())
