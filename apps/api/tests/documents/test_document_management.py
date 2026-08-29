import pytest
import uuid
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.main import app
from app.core.database import get_db_session
from app.models.organization import Organization
from app.workspace.models import Workspace
from app.projects.models import Project
from app.models.user import User
from app.documents.models import Document, Folder, DocumentFavorite, DocumentShare
from app.search.indexer import SearchIndexer

@pytest.mark.asyncio
async def test_document_management_system(db_session: AsyncSession):
    # 1. Setup Test Organization, Workspace, Project, User
    org_id = uuid.uuid4()
    ws_id = uuid.uuid4()
    proj_id = uuid.uuid4()
    user_id = uuid.uuid4()

    org = Organization(id=org_id, name="Test Document Org", slug=f"doc-org-{uuid.uuid4().hex[:6]}")
    ws = Workspace(id=ws_id, organization_id=org_id, name="Test Document Workspace", slug=f"doc-ws-{uuid.uuid4().hex[:6]}")
    proj = Project(id=proj_id, organization_id=org_id, workspace_id=ws_id, name="Test Document Project", slug=f"doc-proj-{uuid.uuid4().hex[:6]}")
    user = User(id=user_id, email=f"doc_user_{uuid.uuid4().hex[:6]}@example.com", username=f"docuser_{uuid.uuid4().hex[:6]}", hashed_password="hashed_pass_123", first_name="Doc", last_name="User")

    from app.models.organization_member import OrganizationMember
    from app.models.role import Role
    from app.workspace.models import WorkspaceMember
    role = Role(id=uuid.uuid4(), name="MEMBER", description="Member Role")
    org_member = OrganizationMember(id=uuid.uuid4(), organization_id=org_id, user_id=user_id, role_id=role.id)
    ws_member = WorkspaceMember(id=uuid.uuid4(), workspace_id=ws_id, user_id=user_id, role="MEMBER")

    db_session.add_all([org, ws, proj, user, role, org_member, ws_member])
    await db_session.commit()

    # 2. Test Folder Creation
    folder = Folder(
        id=uuid.uuid4(),
        organization_id=org_id,
        workspace_id=ws_id,
        name="Engineering Specifications",
        created_by=user_id
    )
    db_session.add(folder)
    await db_session.commit()

    # 3. Test File Upload via DocumentService
    from app.documents.service import DocumentService
    doc_service = DocumentService(db_session)

    test_content = b"print('Hello MindMesh Knowledge Intelligence System')"
    uploaded_doc = await doc_service.upload_document(
        file_content=test_content,
        filename="app_script.py",
        content_type="text/x-python",
        org_id=org_id,
        workspace_id=ws_id,
        project_id=proj_id,
        folder_id=folder.id,
        user_id=user_id,
        title="App Script Code",
        visibility="private"
    )

    assert uploaded_doc.id is not None
    assert uploaded_doc.filename == "app_script.py"
    assert uploaded_doc.extension == "py"
    assert uploaded_doc.size == len(test_content)
    assert uploaded_doc.folder_id == folder.id

    # 4. Test SHA-256 Duplicate Detection
    duplicate_doc = await doc_service.upload_document(
        file_content=test_content,
        filename="app_script_copy.py",
        content_type="text/x-python",
        org_id=org_id,
        workspace_id=ws_id,
        project_id=proj_id,
        folder_id=folder.id,
        user_id=user_id
    )
    assert duplicate_doc.id == uploaded_doc.id # Deduplication returned identical doc

    # 5. Test Executable Extension Rejection Security Validation
    from app.documents.exceptions import InvalidFileException
    with pytest.raises(InvalidFileException) as exc_info:
        await doc_service.upload_document(
            file_content=b"malicious content",
            filename="malware.exe",
            content_type="application/x-msdownload",
            org_id=org_id,
            workspace_id=ws_id,
            project_id=proj_id,
            user_id=user_id
        )
    assert "Security violation" in str(exc_info.value)

    # 6. Test Universal Search Indexing Verification
    from app.search.service import SearchService
    search_service = SearchService(db_session)
    search_res = await search_service.universal_search(
        user=user,
        query="app_script",
        entity_type="document",
        workspace_id=ws_id,
        organization_id=org_id
    )
    total_hits = search_res.get("total_hits", 0) if isinstance(search_res, dict) else getattr(search_res, "total_hits", 0)
    results = search_res.get("results", []) if isinstance(search_res, dict) else getattr(search_res, "results", [])
    assert total_hits > 0
    assert any(str(r.get("entity_id") if isinstance(r, dict) else r.entity_id) == str(uploaded_doc.id) for r in results)

    # 7. Test Favorite Toggle
    is_fav = await doc_service.toggle_favorite(user_id, uploaded_doc.id)
    assert is_fav is True
    fav_docs = await doc_service.get_favorite_documents(user_id, org_id)
    assert len(fav_docs) == 1
    assert fav_docs[0].id == uploaded_doc.id

    # 8. Test Document Sharing
    shared_user_id = uuid.uuid4()
    share = await doc_service.share_document(uploaded_doc.id, shared_user_id, "read")
    assert share.shared_with_user_id == shared_user_id
    assert uploaded_doc.visibility == "shared"

    # 9. Test Soft Delete & Restore
    await doc_service.soft_delete_document(uploaded_doc.id)
    trash_docs = await doc_service.list_documents(org_id=org_id, workspace_id=ws_id, is_trash=True)
    assert len(trash_docs) == 1
    assert trash_docs[0].id == uploaded_doc.id

    restored_doc = await doc_service.restore_document(uploaded_doc.id)
    assert restored_doc.deleted_at is None
    active_docs = await doc_service.list_documents(org_id=org_id, workspace_id=ws_id, is_trash=False)
    assert len(active_docs) == 1

    print("Document Management System Verification completed successfully!")
