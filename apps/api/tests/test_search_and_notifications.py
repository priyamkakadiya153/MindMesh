import pytest
from uuid import uuid4
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.user import User
from app.models.session import UserSession
from app.models.organization import Organization
from app.models.organization_member import OrganizationMember
from app.models.conversations import Conversation, ConversationMember, DirectMessage
from app.models.attachments import Attachment
from app.projects.models import Project
from app.notifications.models import Notification
from app.activity.models import ActivityLog
from app.core.security import create_access_token

@pytest.mark.asyncio
async def test_global_search_and_saved_searches(client, db_session: AsyncSession):
    user = User(id=uuid4(), email=f"search_{uuid4().hex[:6]}@example.com", username=f"search_{uuid4().hex[:6]}", hashed_password="h", first_name="Search", last_name="Master")
    db_session.add(user)
    await db_session.commit()

    org_id = uuid4()
    org = Organization(id=org_id, name="Search Org", slug=f"search-org-{uuid4().hex[:6]}", owner_id=user.id)
    m = OrganizationMember(id=uuid4(), organization_id=org_id, user_id=user.id, role="owner")
    ws_id = uuid4()
    conv_id = uuid4()
    conv = Conversation(id=conv_id, organization_id=org_id, workspace_id=ws_id, type="group", name="Alpha Project")
    cm = ConversationMember(id=uuid4(), conversation_id=conv_id, user_id=user.id, role="owner")
    msg = DirectMessage(id=uuid4(), conversation_id=conv_id, sender_id=user.id, organization_id=org_id, workspace_id=ws_id, content="Alpha launch roadmap document")
    att = Attachment(id=uuid4(), organization_id=org_id, workspace_id=ws_id, conversation_id=conv_id, uploaded_by=user.id, original_filename="Alpha_Report.pdf", storage_filename="s", mime_type="application/pdf", file_size=1024, storage_path="p")
    proj = Project(id=uuid4(), organization_id=org_id, workspace_id=ws_id, name="Project Alpha", slug=f"proj-alpha-{uuid4().hex[:6]}", description="Key initiative")

    db_session.add_all([org, m, conv, cm, msg, att, proj])
    await db_session.commit()

    sess = UserSession(id=uuid4(), user_id=user.id, refresh_token_hash="tok_s", expires_at=datetime.utcnow() + timedelta(days=1))
    db_session.add(sess)
    await db_session.commit()

    token = create_access_token(subject=user.id, session_id=sess.id)
    headers = {"Authorization": f"Bearer {token}"}

    # 1. Global Search query "Alpha"
    search_res = await client.get(f"/api/v1/search?q=Alpha&organization_id={org_id}", headers=headers)
    assert search_res.status_code == 200, search_res.text
    data = search_res.json()
    assert data["total_results"] >= 3

    # 2. Message Search query "roadmap"
    msg_search = await client.get(f"/api/v1/search/messages?q=roadmap&organization_id={org_id}", headers=headers)
    assert msg_search.status_code == 200
    assert len(msg_search.json()["items"]) == 1

    # 3. File Search query "Report"
    file_search = await client.get(f"/api/v1/search/files?q=Report&organization_id={org_id}", headers=headers)
    assert file_search.status_code == 200
    assert len(file_search.json()["items"]) == 1

    # 4. Save Search
    save_res = await client.post(f"/api/v1/search/saved?organization_id={org_id}", json={"name": "Alpha Items", "query_text": "Alpha"}, headers=headers)
    assert save_res.status_code == 201

    get_saved = await client.get(f"/api/v1/search/saved?organization_id={org_id}", headers=headers)
    assert get_saved.status_code == 200
    assert len(get_saved.json()) == 1

    # 5. Recent Searches
    get_recent = await client.get(f"/api/v1/search/recent?organization_id={org_id}", headers=headers)
    assert get_recent.status_code == 200
    assert "Alpha" in get_recent.json()

@pytest.mark.asyncio
async def test_notifications_and_activity_feed(client, db_session: AsyncSession):
    user = User(id=uuid4(), email=f"notif_{uuid4().hex[:6]}@example.com", username=f"notif_{uuid4().hex[:6]}", hashed_password="h")
    db_session.add(user)
    await db_session.commit()

    org_id = uuid4()
    org = Organization(id=org_id, name="Notif Org", slug=f"notif-org-{uuid4().hex[:6]}", owner_id=user.id)
    m = OrganizationMember(id=uuid4(), organization_id=org_id, user_id=user.id, role="owner")
    db_session.add_all([org, m])
    await db_session.commit()

    # Create Notifications
    n1 = Notification(id=uuid4(), user_id=user.id, type="mention", title="You were mentioned", message="Hello @user", is_read=False)
    n2 = Notification(id=uuid4(), user_id=user.id, type="new_message", title="New message", message="Hey there", is_read=False)
    db_session.add_all([n1, n2])

    # Create Activity Log
    act = ActivityLog(id=uuid4(), organization_id=org_id, user_id=user.id, event_type="Created project Alpha", entity_type="project", entity_id=uuid4())
    db_session.add(act)
    await db_session.commit()


    sess = UserSession(id=uuid4(), user_id=user.id, refresh_token_hash="tok_n", expires_at=datetime.utcnow() + timedelta(days=1))
    db_session.add(sess)
    await db_session.commit()

    token = create_access_token(subject=user.id, session_id=sess.id)
    headers = {"Authorization": f"Bearer {token}"}

    # 1. Fetch Notifications
    notif_res = await client.get("/api/v1/notifications", headers=headers)
    assert notif_res.status_code == 200
    assert notif_res.json()["unread_count"] == 2

    # 2. Mark Single Read
    read_res = await client.patch(f"/api/v1/notifications/{n1.id}/read", headers=headers)
    assert read_res.status_code == 200

    # 3. Mark All Read
    read_all = await client.patch("/api/v1/notifications/read-all", headers=headers)
    assert read_all.status_code == 200

    # 4. Activity Feed
    act_res = await client.get(f"/api/v1/notifications/activity?organization_id={org_id}", headers=headers)
    assert act_res.status_code == 200
    assert len(act_res.json()) == 1
    assert act_res.json()[0]["action"] == "Created project Alpha"
