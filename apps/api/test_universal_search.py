import asyncio
import os
import sys
import uuid
from datetime import datetime

# Add app to python path
sys.path.insert(0, os.path.abspath("."))

from app.core.database import AsyncSessionLocal, engine
from app.database.base import Base
from app.models.user import User
from app.models.organization import Organization
from app.models.organization_member import OrganizationMember
from app.workspace.models import Workspace, WorkspaceMember
from app.projects.models import Project
from app.models.document import Document
from app.models.task import Task
from app.models.search import SearchIndex, SearchHistory
from app.search.service import SearchService
from app.search.indexer import SearchIndexer

async def test_search_system():
    print("--- Starting MindMesh Universal Search Test ---")

    # 1. Create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with AsyncSessionLocal() as session:
        # Create test Org
        org = Organization(name="Acme Corp", slug=f"acme-{uuid.uuid4().hex[:6]}")
        session.add(org)
        await session.commit()
        await session.refresh(org)

        # Create test User
        user = User(email=f"alice-{uuid.uuid4().hex[:6]}@acme.com", username=f"alice-{uuid.uuid4().hex[:6]}", hashed_password="hash")
        session.add(user)
        await session.commit()
        await session.refresh(user)

        # Create test Role
        from app.models.role import Role
        role_name = f"Admin-{uuid.uuid4().hex[:6]}"
        role = Role(name=role_name, permissions=[])
        session.add(role)
        await session.commit()
        await session.refresh(role)


        # Add user to Org
        org_member = OrganizationMember(organization_id=org.id, user_id=user.id, role_id=role.id)
        session.add(org_member)


        # Create test Workspace
        ws = Workspace(organization_id=org.id, name="Engineering WS", slug=f"eng-{uuid.uuid4().hex[:6]}")
        session.add(ws)
        await session.commit()
        await session.refresh(ws)

        # Add user to Workspace
        ws_member = WorkspaceMember(workspace_id=ws.id, user_id=user.id, role="ADMIN")
        session.add(ws_member)
        await session.commit()

        # Seed sample domain entities
        proj = Project(
            workspace_id=ws.id,
            organization_id=org.id,
            name="Invoice Processing Automation",
            description="Automated invoice parsing and workflow approvals system.",
            slug=f"invoice-auto-{uuid.uuid4().hex[:6]}"
        )
        session.add(proj)
        await session.commit()
        await session.refresh(proj)

        doc = Document(
            organization_id=org.id,
            workspace_id=ws.id,
            project_id=proj.id,
            uploaded_by=user.id,
            title="Invoice_Q3_2026.pdf",
            filename="Invoice_Q3_2026.pdf",
            original_filename="Invoice_Q3_2026.pdf",
            mime_type="application/pdf",
            extension="pdf",
            size=10240,
            checksum_sha256="abc123sha256hash",
            storage_provider="local",
            storage_path="/storage/documents/invoice.pdf",
            processing_status="COMPLETED",
            visibility="private"
        )
        session.add(doc)

        task = Task(
            organization_id=org.id,
            project_id=proj.id,
            description="Verify all vendor invoice line items before month-end settlement.",
            status="open"
        )
        session.add(task)


        await session.commit()
        await session.refresh(doc)
        await session.refresh(task)


        print("--> Created test Organization, Workspace, User, Document, Project, Task.")

        # Seed search index via SearchIndexer
        print("--> Running SearchIndexer.auto_seed_index()...")
        count = await SearchIndexer.auto_seed_index(session)
        print(f"--> Auto-seeded {count} records into search_index.")

        # Test 1: Universal Search (query="invoice", type="all")
        service = SearchService(session)
        res = await service.universal_search(
            user=user,
            query="invoice",
            entity_type="all",
            organization_id=org.id,
            page=1,
            limit=10
        )

        print(f"--> Search query='invoice' returned {res['total_hits']} hits in {res['query_time_ms']} ms:")
        for idx, item in enumerate(res["results"], 1):
            print(f"    {idx}. [{item['entity_type'].upper()}] {item['title']} (Score: {item['score']}, WS: {item.get('workspace_name')})")

        assert res["total_hits"] >= 3, f"Expected at least 3 hits for 'invoice', got {res['total_hits']}"

        # Test 2: Autocomplete suggestions for "inv"
        suggestions = await service.get_suggestions(
            user=user,
            query_prefix="inv",
            organization_id=org.id,
            limit=5
        )
        print("--> Autocomplete suggestions for 'inv':")
        for s in suggestions:
            print(f"    - {s['title']} ({s['type']})")

        assert len(suggestions) >= 2, "Expected at least 2 autocomplete suggestions"

        # Test 3: User Search History
        history = await service.get_user_search_history(user.id)
        print("--> User Search History:")
        for h in history:
            print(f"    - Query: '{h['query']}' at {h['created_at']}")

        assert len(history) >= 1, "Expected search query to be recorded in search history"

        # Test 4: Permission Isolation (Unassociated User)
        other_user = User(email=f"bob-{uuid.uuid4().hex[:6]}@other.com", username=f"bob-{uuid.uuid4().hex[:6]}", hashed_password="hash")

        session.add(other_user)
        await session.commit()
        await session.refresh(other_user)

        res_isolated = await service.universal_search(
            user=other_user,
            query="invoice",
            organization_id=org.id,  # Other user is not a member of org or workspace
            page=1,
            limit=10
        )
        print(f"--> Permission isolation test for unauthorized user: returned {res_isolated['total_hits']} hits (expected 0).")
        assert res_isolated["total_hits"] == 0, "Unauthorized user must receive 0 hits due to RBAC"

        # Test 5: Clear History
        await service.clear_user_search_history(user.id)
        history_after = await service.get_user_search_history(user.id)
        assert len(history_after) == 0, "Search history should be cleared"
        print("--> Search history cleared successfully.")

        print("\nALL UNIVERSAL SEARCH TESTS PASSED SUCCESSFULLY!")


if __name__ == "__main__":
    asyncio.run(test_search_system())
