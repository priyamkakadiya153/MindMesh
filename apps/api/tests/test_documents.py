import pytest
import pytest_asyncio
from io import BytesIO
from uuid import uuid4, UUID
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.documents.models import Document, DocumentUploadJob
from app.documents.enums import ProcessingStatus, DocumentVisibility
from app.models.user import User
from app.models.organization import Organization
from app.models.organization_member import OrganizationMember
from app.models.role import Role
from app.models.project import Project
from app.workspace.models import Workspace
from app.core.security import create_access_token
from passlib.hash import bcrypt

@pytest_asyncio.fixture
async def seeded_doc_data(db_session: AsyncSession):
    from datetime import datetime, timedelta
    from app.models.session import UserSession

    role = Role(name="SUPER_ADMIN", description="Super Admin Role")
    db_session.add(role)
    
    hashed_pwd = bcrypt.hash("password123")
    user = User(username="docuser", email="doc@example.com", hashed_password=hashed_pwd)
    db_session.add(user)
    
    other_user = User(username="otheruser", email="other@example.com", hashed_password=hashed_pwd)
    db_session.add(other_user)
    
    await db_session.flush()

    org = Organization(name="Doc Org", slug="doc-org", owner_id=user.id)
    db_session.add(org)
    
    other_org = Organization(name="Other Doc Org", slug="other-doc-org", owner_id=other_user.id)
    db_session.add(other_org)
    
    await db_session.flush()

    member = OrganizationMember(organization_id=org.id, user_id=user.id, role_id=role.id)
    db_session.add(member)
    
    other_member = OrganizationMember(organization_id=other_org.id, user_id=other_user.id, role_id=role.id)
    db_session.add(other_member)
    
    await db_session.flush()

    ws = Workspace(name="Doc WS", slug="doc-ws", organization_id=org.id)
    db_session.add(ws)
    await db_session.flush()

    proj = Project(name="Doc Proj", slug="doc-proj", workspace_id=ws.id, organization_id=org.id)
    db_session.add(proj)
    await db_session.flush()

    sess = UserSession(id=uuid4(), user_id=user.id, refresh_token_hash="doc_hash_1", expires_at=datetime.utcnow() + timedelta(days=1))
    other_sess = UserSession(id=uuid4(), user_id=other_user.id, refresh_token_hash="doc_hash_2", expires_at=datetime.utcnow() + timedelta(days=1))
    db_session.add_all([sess, other_sess])

    await db_session.commit()

    return {
        "user": user,
        "other_user": other_user,
        "org": org,
        "other_org": other_org,
        "workspace": ws,
        "project": proj,
        "sess": sess,
        "other_sess": other_sess
    }

@pytest.mark.asyncio
async def test_upload_document_success(client: AsyncClient, seeded_doc_data: dict, db_session: AsyncSession):
    user = seeded_doc_data["user"]
    org = seeded_doc_data["org"]
    ws = seeded_doc_data["workspace"]
    proj = seeded_doc_data["project"]
    sess = seeded_doc_data["sess"]
    token = create_access_token(data={"sub": str(user.id), "session_id": str(sess.id)})
    
    headers = {
        "Authorization": f"Bearer {token}",
        "X-Organization-ID": str(org.id)
    }

    files = {
        "file": ("test_doc.pdf", b"pdf mock file bytes content", "application/pdf")
    }
    data = {
        "workspace_id": str(ws.id),
        "project_id": str(proj.id)
    }

    response = await client.post("/api/v1/documents/upload", files=files, data=data, headers=headers)
    assert response.status_code == 201
    res_data = response.json()
    assert res_data["filename"] == "test_doc.pdf"
    assert res_data["mime_type"] == "application/pdf"
    assert res_data["extension"] == "pdf"
    assert res_data["processing_status"] in ("QUEUED", "COMPLETED", "READY", "queued", "completed", "ready")
    assert res_data["organization_id"] == str(org.id)
    assert res_data["workspace_id"] == str(ws.id)
    assert res_data["project_id"] == str(proj.id)

    # Verify db records
    stmt = select(Document).where(Document.id == UUID(res_data["id"]))
    doc = (await db_session.execute(stmt)).scalar_one_or_none()
    assert doc is not None
    assert doc.filename == "test_doc.pdf"
    assert doc.size == len(b"pdf mock file bytes content")

    # Verify upload jobs initialized
    stmt_job = select(DocumentUploadJob).where(DocumentUploadJob.document_id == doc.id)
    job = (await db_session.execute(stmt_job)).scalar_one_or_none()
    assert job is not None
    assert job.status in ("QUEUED", "COMPLETED", "READY", "queued", "completed", "ready", ProcessingStatus.QUEUED, ProcessingStatus.READY)

@pytest.mark.asyncio
async def test_upload_invalid_mime_type(client: AsyncClient, seeded_doc_data: dict):
    user = seeded_doc_data["user"]
    org = seeded_doc_data["org"]
    ws = seeded_doc_data["workspace"]
    proj = seeded_doc_data["project"]
    sess = seeded_doc_data["sess"]
    token = create_access_token(data={"sub": str(user.id), "session_id": str(sess.id)})
    headers = {
        "Authorization": f"Bearer {token}",
        "X-Organization-ID": str(org.id)
    }

    files = {
        "file": ("test_danger.exe", b"executable bytes", "application/x-msdownload")
    }
    data = {
        "workspace_id": str(ws.id),
        "project_id": str(proj.id)
    }

    response = await client.post("/api/v1/documents/upload", files=files, data=data, headers=headers)
    assert response.status_code == 400
    assert "extension" in response.json()["detail"].lower() or "media content type" in response.json()["detail"].lower()

@pytest.mark.asyncio
async def test_upload_empty_file(client: AsyncClient, seeded_doc_data: dict):
    user = seeded_doc_data["user"]
    org = seeded_doc_data["org"]
    ws = seeded_doc_data["workspace"]
    proj = seeded_doc_data["project"]
    sess = seeded_doc_data["sess"]
    token = create_access_token(data={"sub": str(user.id), "session_id": str(sess.id)})
    headers = {
        "Authorization": f"Bearer {token}",
        "X-Organization-ID": str(org.id)
    }

    files = {
        "file": ("test_empty.pdf", b"", "application/pdf")
    }
    data = {
        "workspace_id": str(ws.id),
        "project_id": str(proj.id)
    }

    response = await client.post("/api/v1/documents/upload", files=files, data=data, headers=headers)
    assert response.status_code == 400
    assert "empty file" in response.json()["detail"].lower()

@pytest.mark.asyncio
async def test_get_document_details(client: AsyncClient, seeded_doc_data: dict, db_session: AsyncSession):
    user = seeded_doc_data["user"]
    org = seeded_doc_data["org"]
    ws = seeded_doc_data["workspace"]
    proj = seeded_doc_data["project"]
    
    doc = Document(
        organization_id=org.id,
        workspace_id=ws.id,
        project_id=proj.id,
        uploaded_by=user.id,
        filename="existing.txt",
        original_filename="existing.txt",
        mime_type="text/plain",
        extension="txt",
        size=100,
        checksum_sha256="abc123sha",
        storage_provider="local",
        storage_path="local/path/existing.txt",
        processing_status=ProcessingStatus.READY
    )
    db_session.add(doc)
    await db_session.commit()

    sess = seeded_doc_data["sess"]
    token = create_access_token(data={"sub": str(user.id), "session_id": str(sess.id)})
    headers = {
        "Authorization": f"Bearer {token}",
        "X-Organization-ID": str(org.id)
    }

    response = await client.get(f"/api/v1/documents/{doc.id}", headers=headers)
    assert response.status_code == 200
    assert response.json()["filename"] == "existing.txt"
    assert response.json()["checksum_sha256"] == "abc123sha"

@pytest.mark.asyncio
async def test_cross_org_access_denied(client: AsyncClient, seeded_doc_data: dict, db_session: AsyncSession):
    user = seeded_doc_data["user"]
    other_user = seeded_doc_data["other_user"]
    org = seeded_doc_data["org"]
    other_org = seeded_doc_data["other_org"]
    ws = seeded_doc_data["workspace"]
    proj = seeded_doc_data["project"]
    
    doc = Document(
        organization_id=org.id,
        workspace_id=ws.id,
        project_id=proj.id,
        uploaded_by=user.id,
        filename="private.txt",
        original_filename="private.txt",
        mime_type="text/plain",
        extension="txt",
        size=100,
        checksum_sha256="checksum",
        storage_provider="local",
        storage_path="local/path/private.txt"
    )
    db_session.add(doc)
    await db_session.commit()

    other_sess = seeded_doc_data["other_sess"]
    token = create_access_token(data={"sub": str(other_user.id), "session_id": str(other_sess.id)})
    headers = {
        "Authorization": f"Bearer {token}",
        "X-Organization-ID": str(other_org.id)
    }

    response = await client.get(f"/api/v1/documents/{doc.id}", headers=headers)
    assert response.status_code == 404

@pytest.mark.asyncio
async def test_delete_document_soft(client: AsyncClient, seeded_doc_data: dict, db_session: AsyncSession):
    user = seeded_doc_data["user"]
    org = seeded_doc_data["org"]
    ws = seeded_doc_data["workspace"]
    proj = seeded_doc_data["project"]
    
    doc = Document(
        organization_id=org.id,
        workspace_id=ws.id,
        project_id=proj.id,
        uploaded_by=user.id,
        filename="delete_me.txt",
        original_filename="delete_me.txt",
        mime_type="text/plain",
        extension="txt",
        size=100,
        checksum_sha256="checksum_delete",
        storage_provider="local",
        storage_path="local/path/delete_me.txt"
    )
    db_session.add(doc)
    await db_session.commit()

    sess = seeded_doc_data["sess"]
    token = create_access_token(data={"sub": str(user.id), "session_id": str(sess.id)})
    headers = {
        "Authorization": f"Bearer {token}",
        "X-Organization-ID": str(org.id)
    }

    response = await client.delete(f"/api/v1/documents/{doc.id}", headers=headers)
    assert response.status_code == 204

    # Verify soft delete
    stmt = select(Document).where(Document.id == doc.id)
    db_doc = (await db_session.execute(stmt)).scalar_one()
    await db_session.refresh(db_doc)
    assert db_doc.is_active is False

@pytest.mark.asyncio
async def test_document_metadata_workflow(client: AsyncClient, seeded_doc_data: dict, db_session: AsyncSession):
    user = seeded_doc_data["user"]
    org = seeded_doc_data["org"]
    ws = seeded_doc_data["workspace"]
    proj = seeded_doc_data["project"]

    doc = Document(
        organization_id=org.id,
        workspace_id=ws.id,
        project_id=proj.id,
        uploaded_by=user.id,
        filename="meta_test.txt",
        original_filename="meta_test.txt",
        mime_type="text/plain",
        extension="txt",
        size=50,
        checksum_sha256="abc",
        storage_provider="local",
        storage_path="local/path/meta_test.txt"
    )
    db_session.add(doc)
    await db_session.commit()

    sess = seeded_doc_data["sess"]
    token = create_access_token(data={"sub": str(user.id), "session_id": str(sess.id)})
    headers = {
        "Authorization": f"Bearer {token}",
        "X-Organization-ID": str(org.id)
    }

    # GET metadata (lazy initializes)
    response = await client.get(f"/api/v1/documents/{doc.id}/metadata", headers=headers)
    assert response.status_code == 200
    assert response.json()["title"] == "meta_test.txt"

    # PATCH metadata
    payload = {
        "title": "New Title Spec",
        "description": "Premium knowledge asset description",
        "confidentiality": "restricted"
    }
    response_patch = await client.patch(f"/api/v1/documents/{doc.id}/metadata", json=payload, headers=headers)
    assert response_patch.status_code == 200
    assert response_patch.json()["title"] == "New Title Spec"
    assert response_patch.json()["confidentiality"] == "restricted"

@pytest.mark.asyncio
async def test_document_versioning_workflow(client: AsyncClient, seeded_doc_data: dict, db_session: AsyncSession):
    user = seeded_doc_data["user"]
    org = seeded_doc_data["org"]
    ws = seeded_doc_data["workspace"]
    proj = seeded_doc_data["project"]

    doc = Document(
        organization_id=org.id,
        workspace_id=ws.id,
        project_id=proj.id,
        uploaded_by=user.id,
        filename="version_test.txt",
        original_filename="version_test.txt",
        mime_type="text/plain",
        extension="txt",
        size=10,
        checksum_sha256="hash_v1",
        storage_provider="local",
        storage_path="local/path/v1.txt",
        version=1
    )
    db_session.add(doc)
    await db_session.commit()

    sess = seeded_doc_data["sess"]
    token = create_access_token(data={"sub": str(user.id), "session_id": str(sess.id)})
    headers = {
        "Authorization": f"Bearer {token}",
        "X-Organization-ID": str(org.id)
    }

    # Upload version 2
    files = {
        "file": ("version_test_v2.txt", b"v2 file content bytes", "text/plain")
    }
    data = {
        "change_summary": "Added paragraph B"
    }
    response = await client.post(f"/api/v1/documents/{doc.id}/versions", files=files, data=data, headers=headers)
    assert response.status_code == 201
    assert response.json()["version"] == 2

    # Get versions history list
    response_list = await client.get(f"/api/v1/documents/{doc.id}/versions", headers=headers)
    assert response_list.status_code == 200
    assert len(response_list.json()) == 2
    assert response_list.json()[0]["version_number"] == 1
    assert response_list.json()[1]["version_number"] == 2

    # Restore version 1
    response_restore = await client.post(f"/api/v1/documents/{doc.id}/versions/1/restore", headers=headers)
    assert response_restore.status_code == 200
    assert response_restore.json()["version"] == 3
    assert response_restore.json()["checksum_sha256"] == "hash_v1"

@pytest.mark.asyncio
async def test_document_lifecycle_workflow(client: AsyncClient, seeded_doc_data: dict, db_session: AsyncSession):
    user = seeded_doc_data["user"]
    org = seeded_doc_data["org"]
    ws = seeded_doc_data["workspace"]
    proj = seeded_doc_data["project"]

    doc = Document(
        organization_id=org.id,
        workspace_id=ws.id,
        project_id=proj.id,
        uploaded_by=user.id,
        filename="lifecycle.txt",
        original_filename="lifecycle.txt",
        mime_type="text/plain",
        extension="txt",
        size=10,
        checksum_sha256="life_hash",
        storage_provider="local",
        storage_path="local/path/lifecycle.txt",
        processing_status=ProcessingStatus.READY
    )
    db_session.add(doc)
    await db_session.commit()

    sess = seeded_doc_data["sess"]
    token = create_access_token(data={"sub": str(user.id), "session_id": str(sess.id)})
    headers = {
        "Authorization": f"Bearer {token}",
        "X-Organization-ID": str(org.id)
    }

    # Archive document
    response_archive = await client.post(f"/api/v1/documents/{doc.id}/archive", headers=headers)
    assert response_archive.status_code == 200
    assert response_archive.json()["processing_status"] in ("ARCHIVED", "archived", ProcessingStatus.ARCHIVED)

    # Restore document
    response_restore = await client.post(f"/api/v1/documents/{doc.id}/restore", headers=headers)
    assert response_restore.status_code == 200
    assert response_restore.json()["processing_status"] in ("READY", "ready", ProcessingStatus.READY)

@pytest.mark.asyncio
async def test_document_retention_workflow(client: AsyncClient, seeded_doc_data: dict, db_session: AsyncSession):
    user = seeded_doc_data["user"]
    org = seeded_doc_data["org"]
    sess = seeded_doc_data["sess"]
    token = create_access_token(data={"sub": str(user.id), "session_id": str(sess.id)})
    headers = {
        "Authorization": f"Bearer {token}",
        "X-Organization-ID": str(org.id)
    }

    # Update retention policy
    payload = {
        "retention_days": 100,
        "auto_archive": True,
        "auto_delete": False
    }
    response = await client.patch("/api/v1/documents/retention", json=payload, headers=headers)
    assert response.status_code == 200
    assert response.json()["retention_days"] == 100
    assert response.json()["auto_archive"] is True
    assert response.json()["auto_delete"] is False

    # Apply retention policy
    response_apply = await client.post("/api/v1/documents/retention/apply", headers=headers)
    assert response_apply.status_code == 200
    assert "affected_documents_count" in response_apply.json()

