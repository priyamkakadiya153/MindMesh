import pytest
import io
import hashlib
from uuid import uuid4
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.user import User
from app.models.session import UserSession
from app.models.organization import Organization
from app.models.organization_member import OrganizationMember
from app.models.conversations import Conversation, ConversationMember
from app.models.attachments import Attachment, AttachmentAccessLog
from app.core.security import create_access_token

@pytest.mark.asyncio
async def test_file_upload_download_lifecycle(client, db_session: AsyncSession):
    # Setup User & Org
    user = User(id=uuid4(), email=f"uploader_{uuid4().hex[:6]}@example.com", username=f"uploader_{uuid4().hex[:6]}", hashed_password="h", first_name="File", last_name="Uploader")
    db_session.add(user)
    await db_session.commit()

    org_id = uuid4()
    org = Organization(id=org_id, name="File Org", slug=f"file-org-{uuid4().hex[:6]}", owner_id=user.id)
    m = OrganizationMember(id=uuid4(), organization_id=org_id, user_id=user.id, role="owner")
    db_session.add_all([org, m])
    await db_session.commit()

    # Create Conversation
    conv_id = uuid4()
    conv = Conversation(id=conv_id, organization_id=org_id, type="group", name="Design Assets")
    cm = ConversationMember(id=uuid4(), conversation_id=conv_id, user_id=user.id, role="owner")
    db_session.add_all([conv, cm])
    await db_session.commit()

    # Session & Auth token
    sess = UserSession(id=uuid4(), user_id=user.id, refresh_token_hash="tok_f", expires_at=datetime.utcnow() + timedelta(days=1))
    db_session.add(sess)
    await db_session.commit()

    token = create_access_token(subject=user.id, session_id=sess.id)
    headers = {"Authorization": f"Bearer {token}"}

    # 1. Upload File
    file_content = b"MindMesh Knowledge Intelligence System Spec Content"
    file_checksum = hashlib.sha256(file_content).hexdigest()

    upload_res = await client.post(
        "/api/v1/files/upload",
        data={"conversation_id": str(conv_id)},
        files={"file": ("architecture_spec.txt", io.BytesIO(file_content), "text/plain")},
        headers=headers
    )
    assert upload_res.status_code == 201, upload_res.text
    file_data = upload_res.json()
    file_id = file_data["id"]
    assert file_data["original_filename"] == "architecture_spec.txt"
    assert file_data["checksum"] == file_checksum
    assert file_data["file_size"] == len(file_content)

    # 2. Query Shared Files
    list_res = await client.get(f"/api/v1/files?organization_id={org_id}", headers=headers)
    assert list_res.status_code == 200
    list_json = list_res.json()
    items = list_json["items"] if isinstance(list_json, dict) and "items" in list_json else list_json
    assert len(items) == 1
    assert items[0]["id"] == file_id

    # 3. Preview File
    prev_res = await client.get(f"/api/v1/files/{file_id}/preview", headers=headers)
    assert prev_res.status_code == 200
    assert prev_res.content == file_content

    # 4. Download File
    dl_res = await client.get(f"/api/v1/files/{file_id}/download", headers=headers)
    assert dl_res.status_code == 200
    assert dl_res.content == file_content

    # Verify download count increment
    det_res = await client.get(f"/api/v1/files/{file_id}", headers=headers)
    assert det_res.json()["download_count"] == 1

    # 5. Rename File
    rename_res = await client.patch(f"/api/v1/files/{file_id}", json={"original_filename": "renamed_spec.txt"}, headers=headers)
    assert rename_res.status_code == 200
    assert rename_res.json()["original_filename"] == "renamed_spec.txt"

    # 6. Soft Delete & Restore
    del_res = await client.delete(f"/api/v1/files/{file_id}", headers=headers)
    assert del_res.status_code == 200

    rest_res = await client.post(f"/api/v1/files/{file_id}/restore", headers=headers)
    assert rest_res.status_code == 200

@pytest.mark.asyncio
async def test_file_rbac_unauthorized_access(client, db_session: AsyncSession):
    user_a = User(id=uuid4(), email=f"usera_f_{uuid4().hex[:6]}@example.com", username=f"usera_f_{uuid4().hex[:6]}", hashed_password="h")
    user_b = User(id=uuid4(), email=f"userb_f_{uuid4().hex[:6]}@example.com", username=f"userb_f_{uuid4().hex[:6]}", hashed_password="h")
    db_session.add_all([user_a, user_b])
    await db_session.commit()

    org_id = uuid4()
    org = Organization(id=org_id, name="Security Org", slug=f"sec-f-{uuid4().hex[:6]}", owner_id=user_a.id)
    m1 = OrganizationMember(id=uuid4(), organization_id=org_id, user_id=user_a.id, role="owner")
    m2 = OrganizationMember(id=uuid4(), organization_id=org_id, user_id=user_b.id, role="member")
    db_session.add_all([org, m1, m2])
    await db_session.commit()

    # Private conversation owned by A
    conv_id = uuid4()
    conv = Conversation(id=conv_id, organization_id=org_id, type="private", visibility="private")
    cm_a = ConversationMember(id=uuid4(), conversation_id=conv_id, user_id=user_a.id, role="owner")
    db_session.add_all([conv, cm_a])
    await db_session.commit()

    sess_a = UserSession(id=uuid4(), user_id=user_a.id, refresh_token_hash="s_a", expires_at=datetime.utcnow() + timedelta(days=1))
    sess_b = UserSession(id=uuid4(), user_id=user_b.id, refresh_token_hash="s_b", expires_at=datetime.utcnow() + timedelta(days=1))
    db_session.add_all([sess_a, sess_b])
    await db_session.commit()

    token_a = create_access_token(subject=user_a.id, session_id=sess_a.id)
    token_b = create_access_token(subject=user_b.id, session_id=sess_b.id)

    headers_a = {"Authorization": f"Bearer {token_a}"}
    headers_b = {"Authorization": f"Bearer {token_b}"}

    # User A uploads a file to private conversation
    up_res = await client.post(
        "/api/v1/files/upload",
        data={"conversation_id": str(conv_id)},
        files={"file": ("secret.txt", io.BytesIO(b"Confidential"), "text/plain")},
        headers=headers_a
    )
    file_id = up_res.json()["id"]

    # User B (not in conversation) tries to download (Should fail 403)
    dl_res = await client.get(f"/api/v1/files/{file_id}/download", headers=headers_b)
    assert dl_res.status_code == 403
