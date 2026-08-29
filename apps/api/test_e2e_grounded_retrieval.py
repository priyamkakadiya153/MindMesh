import asyncio
import os
import sys
import uuid

sys.path.insert(0, os.path.abspath("."))

from app.core.database import AsyncSessionLocal
from app.models.organization import Organization
from app.models.user import User
from app.workspace.models import Workspace, WorkspaceMember
from app.models.organization_member import OrganizationMember
from app.documents.models import Document
from app.ai.embeddings.models import DocumentChunk
from app.ai.orchestrator import MindMeshAIOrchestrator
from app.models.search import SearchIndex

async def test_e2e_grounded_retrieval():
    print("=== Starting MindMesh Phase 2.3 Required End-to-End Grounding Test ===")

    async with AsyncSessionLocal() as session:
        # Setup tenant
        org = Organization(name="E2E Grounded Org", slug=f"e2e-org-{uuid.uuid4().hex[:6]}")
        session.add(org)
        await session.commit()

        ws = Workspace(organization_id=org.id, name="E2E Workspace", slug=f"e2e-ws-{uuid.uuid4().hex[:6]}")
        session.add(ws)
        await session.commit()

        u_id = uuid.uuid4().hex[:6]
        user = User(
            email=f"e2e_user_{u_id}@mindmesh.com",
            username=f"e2e_user_{u_id}",
            first_name="E2E",
            last_name="Tester",
            hashed_password="mockpassword",
            phone_number=f"+1555{u_id}"
        )
        session.add(user)
        await session.commit()

        session.add(OrganizationMember(organization_id=org.id, user_id=user.id, role="admin", is_active=True))
        session.add(WorkspaceMember(workspace_id=ws.id, user_id=user.id, role="admin", is_active=True))
        await session.commit()

        # 1. Index Document "Authentication Policy"
        doc = Document(
            organization_id=org.id,
            workspace_id=ws.id,
            title="Authentication Policy",
            filename="auth_policy.pdf",
            original_filename="auth_policy.pdf",
            stored_filename="auth_policy_123.pdf",
            mime_type="application/pdf",
            extension="pdf",
            size=1024,
            checksum_sha256="hash_e2e",
            storage_provider="local",
            storage_path="/uploads/auth_policy.pdf"
        )
        session.add(doc)
        await session.commit()

        chunk = DocumentChunk(
            document_id=doc.id,
            organization_id=org.id,
            workspace_id=ws.id,
            chunk_index=1,
            content="Access tokens expire after 15 minutes. Refresh tokens remain valid for 30 days.",
            metadata_json={"page": 1}
        )
        session.add(chunk)
        session.add(SearchIndex(organization_id=org.id, workspace_id=ws.id, entity_type="document", entity_id=doc.id, title=doc.title, content=chunk.content))
        await session.commit()

        orchestrator = MindMeshAIOrchestrator(session)

        # 2. Test Grounded Answer
        res_grounded = await orchestrator.execute(
            user_id=user.id,
            org_id=org.id,
            query="What is our access token expiration policy?",
            workspace_id=ws.id
        )

        print("DEBUG res_grounded answer:", res_grounded.get("answer"))
        print("DEBUG res_grounded grounded:", res_grounded.get("grounded"))
        print("DEBUG res_grounded sources:", res_grounded.get("sources"))
        assert res_grounded["grounded"] == True
        assert len(res_grounded["sources"]) > 0
        print("--> [E2E STEP 1 PASS] Grounded Answer:", res_grounded["answer"])
        print("    Source Title:", res_grounded["sources"][0]["title"])

        # 3. Test Partial Knowledge Refusal ("Who approved the authentication policy?")
        res_missing_approver = await orchestrator.execute(
            user_id=user.id,
            org_id=org.id,
            query="Who approved the authentication policy?",
            workspace_id=ws.id
        )

        assert res_missing_approver["grounded"] == False or "couldn't find enough information" in res_missing_approver["answer"]
        print("--> [E2E STEP 2 PASS] Missing Approver refused without fabrication!")

        # 4. Test Completely Absent Knowledge Refusal ("What is our database migration strategy?")
        res_absent_db = await orchestrator.execute(
            user_id=user.id,
            org_id=org.id,
            query="What is our database migration strategy?",
            workspace_id=ws.id
        )

        assert res_absent_db["grounded"] == False or "couldn't find enough information" in res_absent_db["answer"]
        print("--> [E2E STEP 3 PASS] Absent DB Migration strategy refused without fabrication!")

    print("=== Required End-to-End Grounding Test Passed 100%! ===")

if __name__ == "__main__":
    asyncio.run(test_e2e_grounded_retrieval())
