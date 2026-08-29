import asyncio
import os
import sys
import uuid

sys.path.insert(0, os.path.abspath("."))

from app.core.database import AsyncSessionLocal, engine
from app.models.base import BaseEntity
from app.models.organization import Organization
from app.models.user import User
from app.workspace.models import Workspace, WorkspaceMember
from app.models.organization_member import OrganizationMember
from app.models.conversations import Conversation, ConversationMember, DirectMessage
from app.documents.service import DocumentService
from app.search.service import SearchService
from app.search.indexer import SearchIndexer
from sqlalchemy import select

async def test_universal_search_e2e():
    print("=== Starting MindMesh Phase 2.6 Universal Search E2E Test Suite ===")

    async with engine.begin() as conn:
        await conn.run_sync(BaseEntity.metadata.create_all)

    async with AsyncSessionLocal() as session:
        # 1. Setup Tenant A
        orgA = Organization(name="Universal Search Org A", slug=f"univ-orga-{uuid.uuid4().hex[:6]}")
        session.add(orgA)
        await session.commit()

        wsA = Workspace(organization_id=orgA.id, name="Engineering WS", slug=f"univ-wsa-{uuid.uuid4().hex[:6]}")
        session.add(wsA)
        await session.commit()

        uA_id = uuid.uuid4().hex[:6]
        userA = User(
            email=f"univ_usera_{uA_id}@mindmesh.com",
            username=f"univ_usera_{uA_id}",
            first_name="User",
            last_name="A",
            hashed_password="mockpassword",
            phone_number=f"+1555{uA_id}"
        )
        session.add(userA)
        await session.commit()

        session.add(OrganizationMember(organization_id=orgA.id, user_id=userA.id, role="admin", is_active=True))
        session.add(WorkspaceMember(workspace_id=wsA.id, user_id=userA.id, role="admin", is_active=True))
        await session.commit()

        # 2. Setup Tenant B (Unrelated Org)
        orgB = Organization(name="Universal Search Org B", slug=f"univ-orgb-{uuid.uuid4().hex[:6]}")
        session.add(orgB)
        await session.commit()

        wsB = Workspace(organization_id=orgB.id, name="Org B WS", slug=f"univ-wsb-{uuid.uuid4().hex[:6]}")
        session.add(wsB)
        await session.commit()

        uB_id = uuid.uuid4().hex[:6]
        userB = User(
            email=f"univ_userb_{uB_id}@mindmesh.com",
            username=f"univ_userb_{uB_id}",
            first_name="User",
            last_name="B",
            hashed_password="mockpassword",
            phone_number=f"+1555{uB_id}"
        )
        session.add(userB)
        await session.commit()

        session.add(OrganizationMember(organization_id=orgB.id, user_id=userB.id, role="admin", is_active=True))
        session.add(WorkspaceMember(workspace_id=wsB.id, user_id=userB.id, role="admin", is_active=True))
        await session.commit()

        # -------------------------------------------------------------
        # Section 60 Required E2E Knowledge Seeding
        # -------------------------------------------------------------
        # Seed Document: "Authentication Architecture"
        doc_content = (
            "JWT Authentication Architecture Specification\n\n"
            "JWT access tokens expire after 15 minutes.\n"
            "JWT Token Expiry: 15 minutes.\n"
            "Refresh tokens remain valid for 30 days."
        ).encode("utf-8")

        doc_service = DocumentService(session)
        doc = await doc_service.upload_document(
            file_content=doc_content,
            filename="auth_arch.txt",
            content_type="text/plain",
            org_id=orgA.id,
            workspace_id=wsA.id,
            user_id=userA.id,
            title="Authentication Architecture",
            visibility="private"
        )
        await session.commit()

        # Seed Conversation & DM: "We decided to use PostgreSQL for production."
        conv = Conversation(
            organization_id=orgA.id,
            workspace_id=wsA.id,
            type="group",
            name="Engineering Discussion",
            visibility="private"
        )
        session.add(conv)
        await session.commit()

        session.add(ConversationMember(conversation_id=conv.id, user_id=userA.id, role="admin"))
        await session.commit()

        msg = DirectMessage(
            conversation_id=conv.id,
            sender_id=userA.id,
            organization_id=orgA.id,
            workspace_id=wsA.id,
            content="We decided to use PostgreSQL for production database."
        )
        session.add(msg)
        await session.commit()

        # Index Message & Decision in SearchIndex
        await SearchIndexer.index_entity(
            db=session,
            entity_type="chat",
            entity_id=conv.id,
            title="Engineering Discussion",
            content="We decided to use PostgreSQL for production database.",
            workspace_id=wsA.id,
            organization_id=orgA.id,
            owner_id=userA.id,
            tags=["chat", "message"],
            metadata_json={"chat_id": str(conv.id), "message_id": str(msg.id)}
        )

        await SearchIndexer.index_entity(
            db=session,
            entity_type="decision",
            entity_id=uuid.uuid4(),
            title="PostgreSQL production decision",
            content="PostgreSQL selected as the production database for high concurrency.",
            workspace_id=wsA.id,
            organization_id=orgA.id,
            owner_id=userA.id,
            tags=["decision", "database"],
            metadata_json={"status": "approved"}
        )
        await session.commit()

        # -------------------------------------------------------------
        # Section 60 Required E2E Search Queries
        # -------------------------------------------------------------
        search_service = SearchService(session)

        # 1. Query: "JWT expiry" -> Expected: Authentication Architecture
        res1 = await search_service.universal_search(
            user=userA,
            query="JWT expiry",
            organization_id=orgA.id,
            workspace_id=wsA.id
        )
        print("--> [QUERY 1 PASS] Hits:", res1["total_hits"], "| Top Result:", res1["results"][0]["title"] if res1["results"] else "None")
        assert res1["total_hits"] >= 1
        assert "Authentication Architecture" in [r["title"] for r in res1["results"]]
        assert res1["results"][0]["deep_link"].startswith("/files?preview=") or "preview=" in res1["results"][0]["deep_link"]

        # 2. Query: "database decision" -> Expected: PostgreSQL decision
        res2 = await search_service.universal_search(
            user=userA,
            query="database decision",
            organization_id=orgA.id,
            workspace_id=wsA.id
        )
        print("--> [QUERY 2 PASS] Hits:", res2["total_hits"], "| Top Result:", res2["results"][0]["title"] if res2["results"] else "None")
        assert res2["total_hits"] >= 1
        assert any("postgresql" in r["title"].lower() or "database" in r["title"].lower() for r in res2["results"])

        # 3. Query: "how long do access tokens last?" -> Expected: Authentication Architecture
        res3 = await search_service.universal_search(
            user=userA,
            query="how long do access tokens last?",
            organization_id=orgA.id,
            workspace_id=wsA.id
        )
        print("--> [QUERY 3 PASS] Hits:", res3["total_hits"], "| Top Result:", res3["results"][0]["title"] if res3["results"] else "None")
        assert res3["total_hits"] >= 1
        assert "Authentication Architecture" in [r["title"] for r in res3["results"]]

        # 4. Query: "what did the team decide about PostgreSQL?" -> Expected: Conversation / Decision
        res4 = await search_service.universal_search(
            user=userA,
            query="what did the team decide about PostgreSQL?",
            organization_id=orgA.id,
            workspace_id=wsA.id
        )
        print("--> [QUERY 4 PASS] Hits:", res4["total_hits"], "| Top Result:", res4["results"][0]["title"] if res4["results"] else "None")
        assert res4["total_hits"] >= 1

        # -------------------------------------------------------------
        # Security Isolation Test (User B from Org B searches Org A content)
        # -------------------------------------------------------------
        res_sec_b = await search_service.universal_search(
            user=userB,
            query="Authentication Architecture JWT expiry",
            organization_id=orgB.id,
            workspace_id=wsB.id
        )
        print("--> [SECURITY TEST ORG B PASS] Hits for User B:", res_sec_b["total_hits"])
        assert res_sec_b["total_hits"] == 0

        # -------------------------------------------------------------
        # Autocomplete & Search History Test
        # -------------------------------------------------------------
        sugg = await search_service.get_suggestions(
            user=userA,
            query_prefix="auth",
            organization_id=orgA.id
        )
        print("--> [AUTOCOMPLETE PASS] Suggestions:", [s["title"] for s in sugg])
        assert len(sugg) >= 1
        assert any("auth" in s["title"].lower() for s in sugg)

        history = await search_service.get_user_search_history(user_id=userA.id)
        print("--> [SEARCH HISTORY PASS] User History:", [h["query"] for h in history])
        assert len(history) >= 1
        assert any("jwt" in h["query"].lower() for h in history)

        # -------------------------------------------------------------
        # Permanent Delete Propagation Test
        # -------------------------------------------------------------
        await doc_service.permanent_delete_document(doc.id)
        await session.commit()

        res_del = await search_service.universal_search(
            user=userA,
            query="Authentication Architecture",
            organization_id=orgA.id,
            workspace_id=wsA.id
        )
        print("--> [DELETE PROPAGATION PASS] Hits after document deletion:", res_del["total_hits"])
        assert not any(r["source_id"] == str(doc.id) for r in res_del["results"])

    print("=== MindMesh Phase 2.6 Universal Search E2E Test Suite Passed 100%! ===")

if __name__ == "__main__":
    asyncio.run(test_universal_search_e2e())
