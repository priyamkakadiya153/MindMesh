import pytest
import pytest_asyncio
from io import BytesIO
from uuid import uuid4
from datetime import datetime, timedelta
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from passlib.hash import bcrypt

from app.models.user import User
from app.models.organization import Organization
from app.models.organization_member import OrganizationMember
from app.models.role import Role
from app.models.session import UserSession
from app.models.conversations import Conversation, ConversationMember
from app.workspace.models import Workspace
from app.core.security import create_access_token
from app.ai.understanding.engine import SemanticUnderstandingEngine
from app.ai.understanding.models import RequestIntent, CapabilityType
from app.ai.capabilities.domain_executors import DomainExecutors

@pytest_asyncio.fixture
async def setup_collaboration_env(db_session: AsyncSession):
    # 1. Roles
    role_admin = Role(name="ADMIN", description="Admin Role")
    role_member = Role(name="MEMBER", description="Member Role")
    db_session.add_all([role_admin, role_member])
    await db_session.flush()

    # 2. Users (Alice & Bob in Org; Charlie in separate Org)
    pwd = bcrypt.hash("securepass123")
    alice = User(username="alice", first_name="Alice", last_name="Smith", email="alice@mesh.com", hashed_password=pwd)
    bob = User(username="bob", first_name="Bob", last_name="Jones", email="bob@mesh.com", hashed_password=pwd)
    charlie = User(username="charlie", first_name="Charlie", last_name="Brown", email="charlie@other.com", hashed_password=pwd)
    db_session.add_all([alice, bob, charlie])
    await db_session.flush()

    # 3. Organizations
    org = Organization(name="Mesh Labs", slug="mesh-labs", owner_id=alice.id)
    other_org = Organization(name="External Corp", slug="external-corp", owner_id=charlie.id)
    db_session.add_all([org, other_org])
    await db_session.flush()

    # 4. Memberships
    mem_alice = OrganizationMember(organization_id=org.id, user_id=alice.id, role_id=role_admin.id)
    mem_bob = OrganizationMember(organization_id=org.id, user_id=bob.id, role_id=role_member.id)
    mem_charlie = OrganizationMember(organization_id=other_org.id, user_id=charlie.id, role_id=role_admin.id)
    db_session.add_all([mem_alice, mem_bob, mem_charlie])
    await db_session.flush()

    # 5. Workspace
    ws = Workspace(name="Main Engineering", slug="main-eng", organization_id=org.id)
    db_session.add(ws)
    await db_session.flush()

    # 6. Conversation (Project Discussion between Alice & Bob)
    conv = Conversation(
        name="Project Discussion",
        type="group",
        organization_id=org.id,
        workspace_id=ws.id,
        owner_id=alice.id
    )
    db_session.add(conv)
    await db_session.flush()

    cm_alice = ConversationMember(conversation_id=conv.id, user_id=alice.id, role="admin")
    cm_bob = ConversationMember(conversation_id=conv.id, user_id=bob.id, role="member")
    db_session.add_all([cm_alice, cm_bob])
    await db_session.flush()

    # 7. User Sessions & Tokens
    sess_alice = UserSession(id=uuid4(), user_id=alice.id, refresh_token_hash="sess_alice", expires_at=datetime.utcnow() + timedelta(days=1))
    sess_bob = UserSession(id=uuid4(), user_id=bob.id, refresh_token_hash="sess_bob", expires_at=datetime.utcnow() + timedelta(days=1))
    sess_charlie = UserSession(id=uuid4(), user_id=charlie.id, refresh_token_hash="sess_charlie", expires_at=datetime.utcnow() + timedelta(days=1))
    db_session.add_all([sess_alice, sess_bob, sess_charlie])
    await db_session.commit()

    token_alice = create_access_token(subject=alice.id, org_id=org.id, session_id=sess_alice.id)
    token_bob = create_access_token(subject=bob.id, org_id=org.id, session_id=sess_bob.id)
    token_charlie = create_access_token(subject=charlie.id, org_id=other_org.id, session_id=sess_charlie.id)

    return {
        "org_id": org.id,
        "other_org_id": other_org.id,
        "ws_id": ws.id,
        "conv_id": conv.id,
        "alice": alice,
        "bob": bob,
        "charlie": charlie,
        "token_alice": token_alice,
        "token_bob": token_bob,
        "token_charlie": token_charlie
    }

@pytest.mark.asyncio
async def test_shared_file_provenance_and_promotion_flow(client: AsyncClient, setup_collaboration_env: dict, db_session: AsyncSession):
    env = setup_collaboration_env
    headers_alice = {"Authorization": f"Bearer {env['token_alice']}"}
    headers_bob = {"Authorization": f"Bearer {env['token_bob']}"}

    # 1. Alice uploads an attachment in the conversation
    file_bytes = b"%PDF-1.5 Architecture Specification content with details on API and database design."
    upload_res = await client.post(
        "/api/v1/files/upload",
        headers=headers_alice,
        data={
            "organization_id": str(env["org_id"]),
            "workspace_id": str(env["ws_id"]),
            "conversation_id": str(env["conv_id"])
        },
        files={"file": ("Architecture_Spec.pdf", file_bytes, "application/pdf")}
    )
    assert upload_res.status_code == 201, upload_res.text
    file_data = upload_res.json()
    file_id = file_data["id"]
    assert file_data["original_filename"] == "Architecture_Spec.pdf"

    # 2. Bob views Shared Files with provenance
    list_res = await client.get(
        f"/api/v1/files?organization_id={env['org_id']}&sharing_filter=shared_with_me",
        headers=headers_bob
    )
    assert list_res.status_code == 200, list_res.text
    list_json = list_res.json()
    items = list_json["items"]
    assert len(items) == 1
    shared_item = items[0]
    assert shared_item["id"] == file_id
    assert shared_item["uploader_name"] == "Alice Smith"
    assert shared_item["source_type"] == "conversation"
    assert shared_item["source_title"] == "Project Discussion"
    assert shared_item["is_promoted_to_document"] is False

    # 3. Bob promotes the shared file into Knowledge Documents
    promote_res = await client.post(
        f"/api/v1/files/{file_id}/promote-to-document",
        headers=headers_bob,
        json={"workspace_id": str(env["ws_id"]), "title": "Promoted Architecture Spec"}
    )
    assert promote_res.status_code == 201, promote_res.text
    promote_data = promote_res.json()
    assert promote_data["status"] == "success"
    assert "document_id" in promote_data
    doc_id = promote_data["document_id"]

    # 4. Bob queries Shared Files again -> verified is_promoted_to_document is True
    list_res_after = await client.get(
        f"/api/v1/files?organization_id={env['org_id']}",
        headers=headers_bob
    )
    assert list_res_after.status_code == 200
    updated_items = list_res_after.json()["items"]
    assert updated_items[0]["is_promoted_to_document"] is True
    assert updated_items[0]["promoted_document_id"] == doc_id

    # 5. Verify Document exists in Knowledge Workspace
    doc_res = await client.get(
        f"/api/v1/documents/{doc_id}",
        headers=headers_bob
    )
    assert doc_res.status_code == 200, doc_res.text
    assert doc_res.json()["title"] == "Promoted Architecture Spec"

@pytest.mark.asyncio
async def test_ai_understanding_and_domain_execution_for_shared_files(setup_collaboration_env: dict, db_session: AsyncSession, client: AsyncClient):
    env = setup_collaboration_env
    headers_alice = {"Authorization": f"Bearer {env['token_alice']}"}

    # Upload attachment API.zip
    upload_res = await client.post(
        "/api/v1/files/upload",
        headers=headers_alice,
        data={
            "organization_id": str(env["org_id"]),
            "workspace_id": str(env["ws_id"]),
            "conversation_id": str(env["conv_id"])
        },
        files={"file": ("API.zip", b"PK0304 mock zip content", "application/zip")}
    )
    assert upload_res.status_code == 201

    # Test 1: Understanding Engine Intent Classification
    u1 = SemanticUnderstandingEngine.parse_request("What files did Alice share with me?")
    assert u1.intent == RequestIntent.SHARED_FILES_QUERY
    assert u1.required_capability == CapabilityType.SHARED_FILES_SERVICE

    u2 = SemanticUnderstandingEngine.parse_request("Who shared API.zip?")
    assert u2.intent == RequestIntent.SHARED_FILES_QUERY
    assert u2.required_capability == CapabilityType.SHARED_FILES_SERVICE

    # Test 2: Domain Executor Execution
    ans = await DomainExecutors.execute_shared_files_query(
        db=db_session,
        org_id=env["org_id"],
        workspace_id=env["ws_id"],
        query="Who shared API.zip?",
        user_id=env["bob"].id
    )
    assert "API.zip" in ans
    assert "Alice Smith" in ans
    assert "Project Discussion" in ans

@pytest.mark.asyncio
async def test_sharing_filters_and_unauthorized_isolation(client: AsyncClient, setup_collaboration_env: dict):
    env = setup_collaboration_env
    headers_alice = {"Authorization": f"Bearer {env['token_alice']}"}
    headers_bob = {"Authorization": f"Bearer {env['token_bob']}"}
    headers_charlie = {"Authorization": f"Bearer {env['token_charlie']}"}

    # Alice uploads
    await client.post(
        "/api/v1/files/upload",
        headers=headers_alice,
        data={
            "organization_id": str(env["org_id"]),
            "workspace_id": str(env["ws_id"]),
            "conversation_id": str(env["conv_id"])
        },
        files={"file": ("confidential_plan.docx", b"Confidential notes", "application/msword")}
    )

    # Bob checks shared_by_me -> 0 items
    res_by_bob = await client.get(
        f"/api/v1/files?organization_id={env['org_id']}&sharing_filter=shared_by_me",
        headers=headers_bob
    )
    assert res_by_bob.status_code == 200
    assert len(res_by_bob.json()["items"]) == 0

    # Alice checks shared_by_me -> 1 item
    res_by_alice = await client.get(
        f"/api/v1/files?organization_id={env['org_id']}&sharing_filter=shared_by_me",
        headers=headers_alice
    )
    assert res_by_alice.status_code == 200
    assert len(res_by_alice.json()["items"]) == 1

    # Charlie from other org is forbidden from listing files from Alice's org
    res_charlie = await client.get(
        f"/api/v1/files?organization_id={env['org_id']}",
        headers=headers_charlie
    )
    assert res_charlie.status_code == 403

    # Charlie in his own org sees 0 files
    res_charlie_own = await client.get(
        f"/api/v1/files?organization_id={env['other_org_id']}",
        headers=headers_charlie
    )
    assert res_charlie_own.status_code == 200
    assert len(res_charlie_own.json()["items"]) == 0
