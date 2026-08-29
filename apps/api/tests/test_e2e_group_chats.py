import pytest
import httpx
from uuid import uuid4
from app.main import app

@pytest.mark.asyncio
async def test_full_group_chat_lifecycle():
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test/api/v1") as client:
        pwd = "Password123!"

        # 1. Register User A (Owner)
        a_email = f"usera_{uuid4().hex[:6]}@example.com"
        resp = await client.post("/auth/register", json={
            "email": a_email,
            "password": pwd,
            "username": f"UserA_{uuid4().hex[:4]}",
            "full_name": "User A"
        })
        assert resp.status_code in (200, 201), f"Register User A failed: {resp.text}"
        a_token = resp.json()["access_token"]
        a_headers = {"Authorization": f"Bearer {a_token}"}
        user_a_id = resp.json()["user"]["id"]

        # 2. Register User B
        b_email = f"userb_{uuid4().hex[:6]}@example.com"
        resp = await client.post("/auth/register", json={
            "email": b_email,
            "password": pwd,
            "username": f"UserB_{uuid4().hex[:4]}",
            "full_name": "User B"
        })
        assert resp.status_code in (200, 201), f"Register User B failed: {resp.text}"
        b_token = resp.json()["access_token"]
        b_headers = {"Authorization": f"Bearer {b_token}"}
        user_b_id = resp.json()["user"]["id"]

        # 3. Register User C
        c_email = f"userc_{uuid4().hex[:6]}@example.com"
        resp = await client.post("/auth/register", json={
            "email": c_email,
            "password": pwd,
            "username": f"UserC_{uuid4().hex[:4]}",
            "full_name": "User C"
        })
        assert resp.status_code in (200, 201), f"Register User C failed: {resp.text}"
        c_token = resp.json()["access_token"]
        c_headers = {"Authorization": f"Bearer {c_token}"}
        user_c_id = resp.json()["user"]["id"]

        # 4. User A creates Organization
        org_name = f"GroupOrg_{uuid4().hex[:6]}"
        org_slug = f"group-org-{uuid4().hex[:6]}"
        resp = await client.post("/organizations/", json={"name": org_name, "slug": org_slug}, headers=a_headers)
        assert resp.status_code in (200, 201), f"Create org failed: {resp.text}"
        org_id = resp.json()["id"]

        # 5. User A invites User B and User C to Organization
        resp = await client.post(f"/organizations/{org_id}/invitations", json={"email": b_email, "role": "admin"}, headers=a_headers)
        assert resp.status_code in (200, 201)
        b_invite_id = resp.json()["id"]

        resp = await client.post(f"/organizations/{org_id}/invitations", json={"email": c_email, "role": "member"}, headers=a_headers)
        assert resp.status_code in (200, 201)
        c_invite_id = resp.json()["id"]

        # 6. User B and User C accept invitations
        resp = await client.post(f"/invitations/{b_invite_id}/accept", headers=b_headers)
        assert resp.status_code == 200

        resp = await client.post(f"/invitations/{c_invite_id}/accept", headers=c_headers)
        assert resp.status_code == 200

        # 7. User A fetches members directory
        resp = await client.get(f"/members?organization_id={org_id}", headers=a_headers)
        assert resp.status_code == 200, f"List members failed: {resp.text}"
        members_list = resp.json()
        assert len(members_list) >= 3

        # 8. User A creates Group Chat with User B
        create_group_payload = {
            "name": "Engineering Leadership",
            "description": "Cross-functional architecture group",
            "organization_id": org_id,
            "visibility": "private",
            "member_user_ids": [user_b_id]
        }
        resp = await client.post("/groups", json=create_group_payload, headers=a_headers)
        assert resp.status_code == 201, f"Create group failed: {resp.text}"
        group_data = resp.json()
        group_id = group_data["id"]
        assert group_data["name"] == "Engineering Leadership"
        assert group_data["member_count"] == 2

        # 9. Verify Group Visibility for User B
        resp = await client.get(f"/groups?organization_id={org_id}", headers=b_headers)
        assert resp.status_code == 200
        b_groups = resp.json()
        b_group_ids = [g["id"] for g in b_groups]
        assert group_id in b_group_ids, "Group should be visible to User B immediately"

        # 10. User A adds User C to group
        resp = await client.post(f"/groups/{group_id}/members", json={"user_id": user_c_id, "role": "member"}, headers=a_headers)
        assert resp.status_code == 200, f"Add member failed: {resp.text}"

        # 11. Verify Group Visibility for User C
        resp = await client.get(f"/groups?organization_id={org_id}", headers=c_headers)
        assert resp.status_code == 200
        c_groups = resp.json()
        c_group_ids = [g["id"] for g in c_groups]
        assert group_id in c_group_ids, "Group should be visible to User C after being added"

        # 12. User A sends group message
        msg_payload = {
            "conversation_id": group_id,
            "content": "Welcome to the Engineering Leadership group!",
            "message_type": "text"
        }
        resp = await client.post("/messages", json=msg_payload, headers=a_headers)
        assert resp.status_code == 201, f"Send message failed: {resp.text}"
        msg_id = resp.json()["id"]

        # 13. User B and User C fetch group message history
        resp = await client.get(f"/messages/{group_id}", headers=b_headers)
        assert resp.status_code == 200
        msgs_b = resp.json()
        assert len(msgs_b) == 1
        assert msgs_b[0]["content"] == "Welcome to the Engineering Leadership group!"

        resp = await client.get(f"/messages/{group_id}", headers=c_headers)
        assert resp.status_code == 200
        msgs_c = resp.json()
        assert len(msgs_c) == 1

        # 14. User B replies to the message in thread
        reply_payload = {"content": "Thanks User A! Super excited for this project."}
        resp = await client.post(f"/messages/{msg_id}/reply", json=reply_payload, headers=b_headers)
        assert resp.status_code == 201

        # 15. User C reacts with an emoji
        resp = await client.post(f"/messages/{msg_id}/react", json={"emoji": "🚀"}, headers=c_headers)
        assert resp.status_code == 200

        # 16. User A edits message
        resp = await client.patch(f"/messages/{msg_id}", json={"content": "Welcome to Engineering Leadership! (Updated)"}, headers=a_headers)
        assert resp.status_code == 200
        assert resp.json()["edited"] is True

        # 17. User A removes User C from group
        resp = await client.delete(f"/groups/{group_id}/members/{user_c_id}", headers=a_headers)
        assert resp.status_code == 200

        # 18. Verify User C can no longer access group details or messages
        resp = await client.get(f"/groups/{group_id}", headers=c_headers)
        assert resp.status_code == 403, "User C should be denied access after removal"

        # 19. User A starts 1-on-1 Private Direct Message with User B
        dm_payload = {
            "target_user_id": user_b_id,
            "organization_id": org_id
        }
        resp = await client.post("/conversations/private", json=dm_payload, headers=a_headers)
        assert resp.status_code == 200, f"Create private DM failed: {resp.text}"
        dm_data = resp.json()
        dm_id = dm_data["id"]
        assert dm_data["type"] == "private"
        assert dm_data["participant"]["id"] == user_b_id

        # 20. User A attempts to start 1-on-1 Private Direct Message with User B AGAIN (Duplicate Prevention)
        resp2 = await client.post("/conversations/private", json=dm_payload, headers=a_headers)
        assert resp2.status_code == 200
        dm_data2 = resp2.json()
        assert dm_data2["id"] == dm_id, "Should reuse the existing 1-on-1 private conversation ID without creating a duplicate"

        # 21. User B lists conversations and sees the 1-on-1 Private Direct Message
        resp = await client.get(f"/conversations?organization_id={org_id}", headers=b_headers)
        assert resp.status_code == 200, f"List conversations failed: {resp.text}"
        b_convs = resp.json()
        b_conv_ids = [c["id"] for c in b_convs]
        assert dm_id in b_conv_ids, "Private DM should appear in User B's conversation sidebar list"

        # 22. User A sends 1-on-1 message to User B
        dm_msg = await client.post("/messages", json={"conversation_id": dm_id, "content": "Hey User B, quick question!", "message_type": "text"}, headers=a_headers)
        assert dm_msg.status_code == 201
        
        # 23. User B retrieves message history and replies
        resp = await client.get(f"/messages/{dm_id}", headers=b_headers)
        assert resp.status_code == 200
        b_msgs = resp.json()
        assert len(b_msgs) == 1
        assert b_msgs[0]["content"] == "Hey User B, quick question!"

        reply_dm = await client.post("/messages", json={"conversation_id": dm_id, "content": "Hey User A! Sure, what's up?", "message_type": "text"}, headers=b_headers)
        assert reply_dm.status_code == 201

        # 24. User A reads User B's message (Read Receipts & Unread Reset)
        read_res = await client.post(f"/conversations/{dm_id}/read", headers=a_headers)
        assert read_res.status_code == 200

        # 25. User A lists conversations to verify unread count is 0
        resp = await client.get(f"/conversations?organization_id={org_id}", headers=a_headers)
        assert resp.status_code == 200
        a_convs = resp.json()
        target_dm = next((c for c in a_convs if c["id"] == dm_id), None)
        assert target_dm is not None
        assert target_dm["unread_count"] == 0
