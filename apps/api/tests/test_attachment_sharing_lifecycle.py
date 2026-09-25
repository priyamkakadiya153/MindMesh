import pytest
import io
import hashlib
from uuid import uuid4
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import User, UserSession, Organization, OrganizationMember, Workspace, WorkspaceMember, Attachment, AttachmentShare
from app.core.security import create_access_token

@pytest.mark.asyncio
async def test_attachment_user_to_user_sharing_flow(client, db_session: AsyncSession):
    # Setup 3 Users: User 1 (Sharer), User 2 (Recipient), User 3 (Unshared Member)
    user1 = User(id=uuid4(), email=f"user1_{uuid4().hex[:6]}@example.com", username=f"user1_{uuid4().hex[:6]}", hashed_password="h", first_name="User", last_name="One")
    user2 = User(id=uuid4(), email=f"user2_{uuid4().hex[:6]}@example.com", username=f"user2_{uuid4().hex[:6]}", hashed_password="h", first_name="User", last_name="Two")
    user3 = User(id=uuid4(), email=f"user3_{uuid4().hex[:6]}@example.com", username=f"user3_{uuid4().hex[:6]}", hashed_password="h", first_name="User", last_name="Three")
    db_session.add_all([user1, user2, user3])
    await db_session.commit()

    # Create Organization & Workspace
    org_id = uuid4()
    org = Organization(id=org_id, name="Shared Files Org", slug=f"sf-org-{uuid4().hex[:6]}", owner_id=user1.id)
    om1 = OrganizationMember(id=uuid4(), organization_id=org_id, user_id=user1.id, role="owner")
    om2 = OrganizationMember(id=uuid4(), organization_id=org_id, user_id=user2.id, role="member")
    om3 = OrganizationMember(id=uuid4(), organization_id=org_id, user_id=user3.id, role="member")

    ws_id = uuid4()
    ws = Workspace(id=ws_id, organization_id=org_id, name="General Workspace", slug=f"ws-{uuid4().hex[:6]}")
    wm1 = WorkspaceMember(id=uuid4(), workspace_id=ws_id, user_id=user1.id, role="admin")
    wm2 = WorkspaceMember(id=uuid4(), workspace_id=ws_id, user_id=user2.id, role="member")
    wm3 = WorkspaceMember(id=uuid4(), workspace_id=ws_id, user_id=user3.id, role="member")

    db_session.add_all([org, om1, om2, om3, ws, wm1, wm2, wm3])
    await db_session.commit()

    # User Sessions and Tokens
    sess1 = UserSession(id=uuid4(), user_id=user1.id, refresh_token_hash="s1", expires_at=datetime.utcnow() + timedelta(days=1))
    sess2 = UserSession(id=uuid4(), user_id=user2.id, refresh_token_hash="s2", expires_at=datetime.utcnow() + timedelta(days=1))
    sess3 = UserSession(id=uuid4(), user_id=user3.id, refresh_token_hash="s3", expires_at=datetime.utcnow() + timedelta(days=1))
    db_session.add_all([sess1, sess2, sess3])
    await db_session.commit()

    token1 = create_access_token(subject=user1.id, session_id=sess1.id)
    token2 = create_access_token(subject=user2.id, session_id=sess2.id)
    token3 = create_access_token(subject=user3.id, session_id=sess3.id)

    headers1 = {"Authorization": f"Bearer {token1}"}
    headers2 = {"Authorization": f"Bearer {token2}"}
    headers3 = {"Authorization": f"Bearer {token3}"}

    # Step 1: User 1 uploads a file (testing.pdf)
    file_content = b"%PDF-1.4 Mock PDF Content for Real User-to-User Sharing Test"
    upload_res = await client.post(
        "/api/v1/files/upload",
        data={"organization_id": str(org_id), "workspace_id": str(ws_id)},
        files={"file": ("testing.pdf", io.BytesIO(file_content), "application/pdf")},
        headers=headers1
    )
    assert upload_res.status_code == 201, upload_res.text
    file_data = upload_res.json()
    file_id = file_data["id"]
    assert file_data["original_filename"] == "testing.pdf"

    # Step 2: Before sharing, User 2 checks "Shared With Me" -> should be empty
    u2_res_before = await client.get(
        f"/api/v1/files?organization_id={org_id}&sharing_filter=shared_with_me",
        headers=headers2
    )
    assert u2_res_before.status_code == 200
    u2_data_before = u2_res_before.json()
    items_before = u2_data_before["items"] if isinstance(u2_data_before, dict) and "items" in u2_data_before else u2_data_before
    assert len(items_before) == 0

    # Step 3: User 1 shares testing.pdf with User 2
    share_res = await client.post(
        f"/api/v1/files/{file_id}/share",
        json={
            "recipient_user_ids": [str(user2.id)],
            "permission": "view"
        },
        headers=headers1
    )
    assert share_res.status_code == 200, f"Share failed: status={share_res.status_code}, text={share_res.text}"
    share_json = share_res.json()
    assert share_json["id"] == file_id
    assert "User Two" in share_json.get("shared_with", [])

    # Step 4: User 2 checks "Shared With Me" -> testing.pdf must appear!
    u2_res_after = await client.get(
        f"/api/v1/files?organization_id={org_id}&sharing_filter=shared_with_me",
        headers=headers2
    )
    assert u2_res_after.status_code == 200
    u2_data_after = u2_res_after.json()
    items_after = u2_data_after["items"] if isinstance(u2_data_after, dict) and "items" in u2_data_after else u2_data_after
    assert len(items_after) == 1
    assert items_after[0]["id"] == file_id
    assert items_after[0]["original_filename"] == "testing.pdf"

    # Step 5: User 1 checks "Shared By Me" -> testing.pdf must appear
    u1_by_me = await client.get(
        f"/api/v1/files?organization_id={org_id}&sharing_filter=shared_by_me",
        headers=headers1
    )
    assert u1_by_me.status_code == 200
    u1_by_me_items = u1_by_me.json()["items"] if isinstance(u1_by_me.json(), dict) and "items" in u1_by_me.json() else u1_by_me.json()
    assert len(u1_by_me_items) == 1
    assert u1_by_me_items[0]["id"] == file_id

    # Step 6: User 2 can preview & download testing.pdf
    prev_res = await client.get(f"/api/v1/files/{file_id}/preview", headers=headers2)
    assert prev_res.status_code == 200
    assert prev_res.content == file_content

    dl_res = await client.get(f"/api/v1/files/{file_id}/download", headers=headers2)
    assert dl_res.status_code == 200
    assert dl_res.content == file_content

    # Step 7: User 3 (unshared member) checks "Shared With Me" -> 0 files
    u3_res = await client.get(
        f"/api/v1/files?organization_id={org_id}&sharing_filter=shared_with_me",
        headers=headers3
    )
    assert u3_res.status_code == 200
    u3_items = u3_res.json()["items"] if isinstance(u3_res.json(), dict) and "items" in u3_res.json() else u3_res.json()
    assert len(u3_items) == 0

    # Step 8: Check list of shares for file
    shares_list_res = await client.get(f"/api/v1/files/{file_id}/shares", headers=headers1)
    assert shares_list_res.status_code == 200
    shares_list = shares_list_res.json()
    assert len(shares_list) == 1
    assert shares_list[0]["user_id"] == str(user2.id)

    # Step 9: User 1 revokes share for User 2
    revoke_res = await client.delete(f"/api/v1/files/{file_id}/share?recipient_user_id={user2.id}", headers=headers1)
    assert revoke_res.status_code == 200

    # User 2 no longer sees it in Shared With Me
    u2_after_revoke = await client.get(
        f"/api/v1/files?organization_id={org_id}&sharing_filter=shared_with_me",
        headers=headers2
    )
    u2_revoked_items = u2_after_revoke.json()["items"] if isinstance(u2_after_revoke.json(), dict) and "items" in u2_after_revoke.json() else u2_after_revoke.json()
    assert len(u2_revoked_items) == 0
