import pytest
import uuid
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from httpx import AsyncClient

from app.models.user import User
from app.models.organization import Organization
from app.models.organization_member import OrganizationMember
from app.workspace.models import Workspace, WorkspaceMember
from app.projects.models import Project, ProjectMember
from app.documents.models import Document, DocumentShare
from app.models.conversations import Conversation, ConversationMember
from app.models.role import Role
from app.models.session import UserSession
from app.models.task import Task
from app.agents.cognitive_repository import CognitiveAgentRepository
from app.agents.cognitive_knowledge import CognitiveAgentKnowledgeService
from app.agents.cognitive_contracts import CognitiveAgentScopeType
from app.core.security import create_access_token


async def seed_ca04_user_and_org(db: AsyncSession, name_prefix: str = "ca04"):
    suffix = uuid.uuid4().hex[:6]

    stmt = select(Role).where(Role.name == "MEMBER")
    res = await db.execute(stmt)
    role = res.scalar_one_or_none()
    if not role:
        role = Role(name="MEMBER", description="Member Role")
        db.add(role)
        await db.flush()

    user = User(
        username=f"{name_prefix}_{suffix}",
        email=f"{name_prefix}_{suffix}@example.com",
        hashed_password="hashed_pwd_123"
    )
    db.add(user)
    await db.flush()

    org = Organization(
        name=f"Org {name_prefix} {suffix}",
        slug=f"org-{name_prefix}-{suffix}",
        owner_id=user.id
    )
    db.add(org)
    await db.flush()

    member = OrganizationMember(organization_id=org.id, user_id=user.id, role_id=role.id)
    db.add(member)
    await db.flush()

    ws = Workspace(
        name=f"Workspace {name_prefix} {suffix}",
        slug=f"ws-{name_prefix}-{suffix}",
        organization_id=org.id,
        created_by=user.id
    )
    db.add(ws)
    await db.flush()

    ws_member = WorkspaceMember(workspace_id=ws.id, user_id=user.id, role="member")
    db.add(ws_member)
    await db.flush()

    sess = UserSession(
        id=uuid.uuid4(),
        user_id=user.id,
        refresh_token_hash=f"session_hash_{suffix}",
        expires_at=datetime.utcnow() + timedelta(days=1)
    )
    db.add(sess)
    await db.commit()

    return user, org, ws, sess


# ---------------- TEST 1: WORKSPACE SCOPE ----------------
@pytest.mark.asyncio
async def test_1_workspace_scope_boundaries(db_session: AsyncSession):
    user, org, ws1, _ = await seed_ca04_user_and_org(db_session, "t1_ws1")
    ws2 = Workspace(name="WS2", slug=f"ws2-{uuid.uuid4().hex[:6]}", organization_id=org.id, created_by=user.id)
    db_session.add(ws2)
    await db_session.flush()
    db_session.add(WorkspaceMember(workspace_id=ws2.id, user_id=user.id, role="member"))
    await db_session.commit()

    # Create document in WS1
    doc1 = Document(
        organization_id=org.id, workspace_id=ws1.id, uploaded_by=user.id,
        title="WS1 Document", filename="ws1.pdf", original_filename="ws1.pdf",
        mime_type="application/pdf", extension="pdf", size=1024, checksum_sha256="abc", storage_path="/path1"
    )
    # Create document in WS2
    doc2 = Document(
        organization_id=org.id, workspace_id=ws2.id, uploaded_by=user.id,
        title="WS2 Document", filename="ws2.pdf", original_filename="ws2.pdf",
        mime_type="application/pdf", extension="pdf", size=1024, checksum_sha256="xyz", storage_path="/path2"
    )
    db_session.add_all([doc1, doc2])
    await db_session.commit()

    agent_ws1 = await CognitiveAgentRepository.create_agent(
        db=db_session, organization_id=org.id, workspace_id=ws1.id, owner_user_id=user.id,
        name="WS1 Agent", instructions="Inst",
        knowledge_scope={"scope_type": "WORKSPACE", "workspace_id": str(ws1.id)}
    )

    resolved = await CognitiveAgentKnowledgeService.resolve_agent_knowledge_boundary(
        db=db_session, agent=agent_ws1, current_user=user, organization_id=org.id, workspace_id=ws1.id
    )

    doc_ids = [d["id"] for d in resolved["accessible_documents"]]
    assert str(doc1.id) in doc_ids
    assert str(doc2.id) not in doc_ids


# ---------------- TEST 2: PROJECT SCOPE ----------------
@pytest.mark.asyncio
async def test_2_project_scope_boundaries(db_session: AsyncSession):
    user, org, ws, _ = await seed_ca04_user_and_org(db_session, "t2")

    proj_a = Project(name="Project A", slug=f"p-a-{uuid.uuid4().hex[:6]}", workspace_id=ws.id, organization_id=org.id, owner_id=user.id)
    proj_b = Project(name="Project B", slug=f"p-b-{uuid.uuid4().hex[:6]}", workspace_id=ws.id, organization_id=org.id, owner_id=user.id)
    db_session.add_all([proj_a, proj_b])
    await db_session.commit()

    doc_a = Document(
        organization_id=org.id, workspace_id=ws.id, project_id=proj_a.id, uploaded_by=user.id,
        title="Doc A", filename="a.pdf", original_filename="a.pdf", mime_type="application/pdf", extension="pdf", size=100, checksum_sha256="11", storage_path="/a"
    )
    doc_b = Document(
        organization_id=org.id, workspace_id=ws.id, project_id=proj_b.id, uploaded_by=user.id,
        title="Doc B", filename="b.pdf", original_filename="b.pdf", mime_type="application/pdf", extension="pdf", size=100, checksum_sha256="22", storage_path="/b"
    )
    db_session.add_all([doc_a, doc_b])
    await db_session.commit()

    agent = await CognitiveAgentRepository.create_agent(
        db=db_session, organization_id=org.id, workspace_id=ws.id, owner_user_id=user.id,
        name="Project A Agent", instructions="Inst",
        knowledge_scope={"scope_type": "PROJECT", "project_id": str(proj_a.id)}
    )

    resolved = await CognitiveAgentKnowledgeService.resolve_agent_knowledge_boundary(
        db=db_session, agent=agent, current_user=user, organization_id=org.id, workspace_id=ws.id
    )

    assert len(resolved["accessible_projects"]) == 1
    assert resolved["accessible_projects"][0]["id"] == str(proj_a.id)
    doc_ids = [d["id"] for d in resolved["accessible_documents"]]
    assert str(doc_a.id) in doc_ids
    assert str(doc_b.id) not in doc_ids


# ---------------- TEST 3: DOCUMENT SCOPE ----------------
@pytest.mark.asyncio
async def test_3_document_scope_boundaries(db_session: AsyncSession):
    user, org, ws, _ = await seed_ca04_user_and_org(db_session, "t3")

    doc1 = Document(organization_id=org.id, workspace_id=ws.id, uploaded_by=user.id, title="Doc 1", filename="1.pdf", original_filename="1.pdf", mime_type="pdf", extension="pdf", size=1, checksum_sha256="1", storage_path="/1")
    doc2 = Document(organization_id=org.id, workspace_id=ws.id, uploaded_by=user.id, title="Doc 2", filename="2.pdf", original_filename="2.pdf", mime_type="pdf", extension="pdf", size=1, checksum_sha256="2", storage_path="/2")
    db_session.add_all([doc1, doc2])
    await db_session.commit()

    agent = await CognitiveAgentRepository.create_agent(
        db=db_session, organization_id=org.id, workspace_id=ws.id, owner_user_id=user.id,
        name="Doc 1 Agent", instructions="Inst",
        knowledge_scope={"scope_type": "DOCUMENT", "document_ids": [str(doc1.id)]}
    )

    resolved = await CognitiveAgentKnowledgeService.resolve_agent_knowledge_boundary(
        db=db_session, agent=agent, current_user=user, organization_id=org.id, workspace_id=ws.id
    )

    doc_ids = [d["id"] for d in resolved["accessible_documents"]]
    assert len(doc_ids) == 1
    assert doc_ids[0] == str(doc1.id)


# ---------------- TEST 4: CONVERSATION SCOPE ----------------
@pytest.mark.asyncio
async def test_4_conversation_scope_boundaries(db_session: AsyncSession):
    user, org, ws, _ = await seed_ca04_user_and_org(db_session, "t4")

    conv1 = Conversation(organization_id=org.id, workspace_id=ws.id, participant_one=user.id, participant_two=uuid.uuid4(), name="Conv 1")
    conv2 = Conversation(organization_id=org.id, workspace_id=ws.id, participant_one=user.id, participant_two=uuid.uuid4(), name="Conv 2")
    db_session.add_all([conv1, conv2])
    await db_session.commit()

    agent = await CognitiveAgentRepository.create_agent(
        db=db_session, organization_id=org.id, workspace_id=ws.id, owner_user_id=user.id,
        name="Conv 1 Agent", instructions="Inst",
        knowledge_scope={"scope_type": "CONVERSATION", "conversation_ids": [str(conv1.id)]}
    )

    resolved = await CognitiveAgentKnowledgeService.resolve_agent_knowledge_boundary(
        db=db_session, agent=agent, current_user=user, organization_id=org.id, workspace_id=ws.id
    )

    conv_ids = [c["id"] for c in resolved["accessible_conversations"]]
    assert len(conv_ids) == 1
    assert conv_ids[0] == str(conv1.id)


# ---------------- TEST 5: PRIVATE DM PROTECTION ----------------
@pytest.mark.asyncio
async def test_5_private_dm_protection(db_session: AsyncSession):
    user_a, org, ws, _ = await seed_ca04_user_and_org(db_session, "t5_a")
    user_b, _, _, _ = await seed_ca04_user_and_org(db_session, "t5_b")

    # Private DM between User B and User C (User A is NOT a participant)
    user_c = uuid.uuid4()
    private_dm = Conversation(organization_id=org.id, workspace_id=ws.id, participant_one=user_b.id, participant_two=user_c, name="Private DM B-C")
    db_session.add(private_dm)
    await db_session.commit()

    agent_a = await CognitiveAgentRepository.create_agent(
        db=db_session, organization_id=org.id, workspace_id=ws.id, owner_user_id=user_a.id,
        name="User A Agent", instructions="Inst",
        knowledge_scope={"scope_type": "CONVERSATION", "conversation_ids": [str(private_dm.id)]}
    )

    # User A tries to resolve agent scope
    resolved = await CognitiveAgentKnowledgeService.resolve_agent_knowledge_boundary(
        db=db_session, agent=agent_a, current_user=user_a, organization_id=org.id, workspace_id=ws.id
    )

    assert len(resolved["accessible_conversations"]) == 0


# ---------------- TEST 6: ORGANIZATION ISOLATION ----------------
@pytest.mark.asyncio
async def test_6_organization_isolation_in_scope(db_session: AsyncSession):
    user_a, org_a, ws_a, _ = await seed_ca04_user_and_org(db_session, "t6_a")
    user_b, org_b, ws_b, _ = await seed_ca04_user_and_org(db_session, "t6_b")

    doc_b = Document(organization_id=org_b.id, workspace_id=ws_b.id, uploaded_by=user_b.id, title="Org B Doc", filename="b.pdf", original_filename="b.pdf", mime_type="pdf", extension="pdf", size=1, checksum_sha256="b", storage_path="/b")
    db_session.add(doc_b)
    await db_session.commit()

    agent_a = await CognitiveAgentRepository.create_agent(
        db=db_session, organization_id=org_a.id, workspace_id=ws_a.id, owner_user_id=user_a.id,
        name="Org A Agent", instructions="Inst",
        knowledge_scope={"scope_type": "DOCUMENT", "document_ids": [str(doc_b.id)]}
    )

    resolved = await CognitiveAgentKnowledgeService.resolve_agent_knowledge_boundary(
        db=db_session, agent=agent_a, current_user=user_a, organization_id=org_a.id, workspace_id=ws_a.id
    )

    assert len(resolved["accessible_documents"]) == 0


# ---------------- TEST 7: WORKSPACE SWITCHING ISOLATION ----------------
@pytest.mark.asyncio
async def test_7_workspace_switching_isolation(client: AsyncClient, db_session: AsyncSession):
    user, org, ws1, sess = await seed_ca04_user_and_org(db_session, "t7_ws1")
    ws2 = Workspace(name="WS2", slug=f"ws2-{uuid.uuid4().hex[:6]}", organization_id=org.id, created_by=user.id)
    db_session.add(ws2)
    await db_session.flush()
    db_session.add(WorkspaceMember(workspace_id=ws2.id, user_id=user.id, role="member"))
    await db_session.commit()

    doc_ws2 = Document(organization_id=org.id, workspace_id=ws2.id, uploaded_by=user.id, title="WS2 Doc", filename="w2.pdf", original_filename="w2.pdf", mime_type="pdf", extension="pdf", size=1, checksum_sha256="w2", storage_path="/w2")
    db_session.add(doc_ws2)
    await db_session.commit()

    agent = await CognitiveAgentRepository.create_agent(
        db=db_session, organization_id=org.id, workspace_id=ws1.id, owner_user_id=user.id,
        name="WS1 Agent", instructions="Inst"
    )

    token = create_access_token(subject=str(user.id), session_id=str(sess.id))
    headers = {"Authorization": f"Bearer {token}", "X-Organization-ID": str(org.id)}

    # Attempt to put WS2 document into WS1 agent's scope via PUT API
    res = await client.put(f"/api/v1/cognitive-agents/{agent.id}/knowledge-scope", json={
        "scope_type": "DOCUMENT",
        "document_ids": [str(doc_ws2.id)]
    }, headers=headers)

    assert res.status_code == 200
    updated_scope = res.json()["knowledge_scope"]
    # Document from WS2 must be stripped out during validation
    assert len(updated_scope["document_ids"]) == 0


# ---------------- TEST 8: STALE / DELETED RESOURCE SAFETY ----------------
@pytest.mark.asyncio
async def test_8_stale_deleted_resource_safety(db_session: AsyncSession):
    user, org, ws, _ = await seed_ca04_user_and_org(db_session, "t8")

    doc = Document(organization_id=org.id, workspace_id=ws.id, uploaded_by=user.id, title="Soft Deleted Doc", filename="d.pdf", original_filename="d.pdf", mime_type="pdf", extension="pdf", size=1, checksum_sha256="d", storage_path="/d")
    db_session.add(doc)
    await db_session.commit()

    agent = await CognitiveAgentRepository.create_agent(
        db=db_session, organization_id=org.id, workspace_id=ws.id, owner_user_id=user.id,
        name="Safety Agent", instructions="Inst",
        knowledge_scope={"scope_type": "DOCUMENT", "document_ids": [str(doc.id)]}
    )

    # Soft delete document
    doc.deleted_at = datetime.utcnow()
    await db_session.commit()

    resolved = await CognitiveAgentKnowledgeService.resolve_agent_knowledge_boundary(
        db=db_session, agent=agent, current_user=user, organization_id=org.id, workspace_id=ws.id
    )

    assert len(resolved["accessible_documents"]) == 0


# ---------------- TEST 9: PERMISSION REVOCATION ----------------
@pytest.mark.asyncio
async def test_9_permission_revocation_denies_access(db_session: AsyncSession):
    user_owner, org, ws, _ = await seed_ca04_user_and_org(db_session, "t9_owner")
    user_viewer, _, _, _ = await seed_ca04_user_and_org(db_session, "t9_viewer")

    # Add user_viewer as workspace member of ws
    db_session.add(WorkspaceMember(workspace_id=ws.id, user_id=user_viewer.id, role="member"))
    await db_session.flush()

    doc = Document(organization_id=org.id, workspace_id=ws.id, uploaded_by=user_owner.id, visibility="private", title="Shared Doc", filename="s.pdf", original_filename="s.pdf", mime_type="pdf", extension="pdf", size=1, checksum_sha256="s", storage_path="/s")
    db_session.add(doc)
    await db_session.flush()

    share = DocumentShare(document_id=doc.id, shared_with_user_id=user_viewer.id, permission_level="read")
    db_session.add(share)
    await db_session.commit()

    agent = await CognitiveAgentRepository.create_agent(
        db=db_session, organization_id=org.id, workspace_id=ws.id, owner_user_id=user_viewer.id,
        name="Viewer Agent", instructions="Inst",
        knowledge_scope={"scope_type": "DOCUMENT", "document_ids": [str(doc.id)]}
    )

    # Initially allowed for user_viewer
    resolved1 = await CognitiveAgentKnowledgeService.resolve_agent_knowledge_boundary(
        db=db_session, agent=agent, current_user=user_viewer, organization_id=org.id, workspace_id=ws.id
    )
    assert len(resolved1["accessible_documents"]) == 1

    # Revoke share
    await db_session.delete(share)
    await db_session.commit()

    # Now denied for user_viewer
    resolved2 = await CognitiveAgentKnowledgeService.resolve_agent_knowledge_boundary(
        db=db_session, agent=agent, current_user=user_viewer, organization_id=org.id, workspace_id=ws.id
    )
    assert len(resolved2["accessible_documents"]) == 0


# ---------------- TEST 10: COMBINED SCOPE UNION ----------------
@pytest.mark.asyncio
async def test_10_combined_scope_union(db_session: AsyncSession):
    user, org, ws, _ = await seed_ca04_user_and_org(db_session, "t10")

    proj = Project(name="Proj", slug=f"proj-{uuid.uuid4().hex[:6]}", workspace_id=ws.id, organization_id=org.id, owner_id=user.id)
    doc = Document(organization_id=org.id, workspace_id=ws.id, uploaded_by=user.id, title="Standalone Doc", filename="st.pdf", original_filename="st.pdf", mime_type="pdf", extension="pdf", size=1, checksum_sha256="st", storage_path="/st")
    db_session.add_all([proj, doc])
    await db_session.commit()

    agent = await CognitiveAgentRepository.create_agent(
        db=db_session, organization_id=org.id, workspace_id=ws.id, owner_user_id=user.id,
        name="Combined Agent", instructions="Inst",
        knowledge_scope={
            "scope_type": "SELECTED_KNOWLEDGE",
            "project_id": str(proj.id),
            "document_ids": [str(doc.id)]
        }
    )

    resolved = await CognitiveAgentKnowledgeService.resolve_agent_knowledge_boundary(
        db=db_session, agent=agent, current_user=user, organization_id=org.id, workspace_id=ws.id
    )

    assert len(resolved["accessible_projects"]) == 1
    assert resolved["accessible_projects"][0]["id"] == str(proj.id)
    assert len(resolved["accessible_documents"]) == 1
    assert resolved["accessible_documents"][0]["id"] == str(doc.id)


# ---------------- TEST 11: UNCONFIGURED EMPTY SCOPE RULE ----------------
@pytest.mark.asyncio
async def test_11_unconfigured_empty_scope_rule(db_session: AsyncSession):
    user, org, ws, _ = await seed_ca04_user_and_org(db_session, "t11")

    # Add documents to workspace
    doc = Document(organization_id=org.id, workspace_id=ws.id, uploaded_by=user.id, title="Doc", filename="d.pdf", original_filename="d.pdf", mime_type="pdf", extension="pdf", size=1, checksum_sha256="d", storage_path="/d")
    db_session.add(doc)
    await db_session.commit()

    # Agent with None / empty knowledge scope
    agent = await CognitiveAgentRepository.create_agent(
        db=db_session, organization_id=org.id, workspace_id=ws.id, owner_user_id=user.id,
        name="Unconfigured Agent", instructions="Inst",
        knowledge_scope=None
    )

    resolved = await CognitiveAgentKnowledgeService.resolve_agent_knowledge_boundary(
        db=db_session, agent=agent, current_user=user, organization_id=org.id, workspace_id=ws.id
    )

    assert resolved["scope_type"] == "NONE"
    assert len(resolved["accessible_projects"]) == 0
    assert len(resolved["accessible_documents"]) == 0
    assert len(resolved["accessible_conversations"]) == 0
    assert "no knowledge access configured" in resolved["message"].lower()


# ---------------- TEST 12: ZERO EXECUTION SIDE EFFECTS ON SCOPE UPDATE ----------------
@pytest.mark.asyncio
async def test_12_zero_execution_side_effects_on_scope_update(client: AsyncClient, db_session: AsyncSession):
    user, org, ws, sess = await seed_ca04_user_and_org(db_session, "t12")
    token = create_access_token(subject=str(user.id), session_id=str(sess.id))
    headers = {"Authorization": f"Bearer {token}", "X-Organization-ID": str(org.id)}

    agent = await CognitiveAgentRepository.create_agent(
        db=db_session, organization_id=org.id, workspace_id=ws.id, owner_user_id=user.id,
        name="Scope Update Agent", instructions="Inst"
    )

    tasks_count_before = (await db_session.execute(select(func.count(Task.id)))).scalar() or 0

    res = await client.put(f"/api/v1/cognitive-agents/{agent.id}/knowledge-scope", json={
        "scope_type": "WORKSPACE"
    }, headers=headers)

    assert res.status_code == 200

    tasks_count_after = (await db_session.execute(select(func.count(Task.id)))).scalar() or 0
    assert tasks_count_after == tasks_count_before
