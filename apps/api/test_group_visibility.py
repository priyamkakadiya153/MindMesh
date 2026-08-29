import asyncio
import os
import sys
from uuid import uuid4
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.database.session import AsyncSessionLocal
from app.models.user import User
from app.models.organization import Organization
from app.models.organization_member import OrganizationMember
from app.models.workspace import Workspace
from app.models.conversations import Conversation, ConversationMember, DirectMessage

from app.conversations.groups_router import (
    create_group, GroupCreatePayload,
    list_groups,
    get_group_details,
    add_group_member, AddMemberPayload
)
from app.conversations.messages_router import send_message, MessageCreatePayload, get_messages_history
from app.conversations.router import mark_conversation_as_read

async def run_group_visibility_tests():
    print("=== Starting MindMesh Phase 1.3 Group Visibility Integration Tests ===")
    async with AsyncSessionLocal() as db:
        suffix = uuid4().hex[:6]
        
        # User 1 and User 2
        user_1 = User(
            id=uuid4(),
            email=f"user1_{suffix}@mindmesh.test",
            username=f"user1_{suffix}",
            hashed_password="hashed_pass_test",
            first_name="User",
            last_name="One",
            is_active=True
        )
        user_2 = User(
            id=uuid4(),
            email=f"user2_{suffix}@mindmesh.test",
            username=f"user2_{suffix}",
            hashed_password="hashed_pass_test",
            first_name="User",
            last_name="Two",
            is_active=True
        )
        db.add_all([user_1, user_2])
        await db.flush()

        org = Organization(
            id=uuid4(),
            name=f"Visibility Test Org {suffix}",
            slug=f"visibility-org-{suffix}",
            created_by=str(user_2.id)
        )
        db.add(org)
        await db.flush()

        # Two workspaces in the same organization
        ws1 = Workspace(id=uuid4(), organization_id=org.id, name="User 1 Workspace", slug=f"ws1-{suffix}")
        ws2 = Workspace(id=uuid4(), organization_id=org.id, name="User 2 Workspace", slug=f"ws2-{suffix}")
        db.add_all([ws1, ws2])

        om_1 = OrganizationMember(id=uuid4(), organization_id=org.id, user_id=user_1.id, role="member")
        om_2 = OrganizationMember(id=uuid4(), organization_id=org.id, user_id=user_2.id, role="owner")
        db.add_all([om_1, om_2])
        await db.commit()

        print("--> Setup test org, 2 workspaces, and 2 users.")

        # TEST A: User 2 creates "demo group" in Workspace 2
        payload_a = GroupCreatePayload(
            name="demo group",
            description="Testing visibility across members and workspaces",
            organization_id=org.id,
            workspace_id=ws2.id,
            visibility="private",
            member_user_ids=[]
        )
        group_resp = await create_group(payload_a, current_user=user_2, db=db)
        group_id = group_resp.id
        print(f"--> TEST A: User 2 created group '{group_resp.name}' (ID: {group_id})")
        assert group_resp.name == "demo group"

        # TEST B: User 2 adds User 1 to "demo group"
        add_resp = await add_group_member(group_id, AddMemberPayload(user_id=user_1.id, role="member"), current_user=user_2, db=db)
        print(f"--> TEST B: User 2 added User 1 to 'demo group'. User 1 membership ID: {add_resp.id}")

        # Check visibility for User 2
        u2_groups = await list_groups(organization_id=org.id, workspace_id=ws2.id, current_user=user_2, db=db)
        u2_group_names = [g.name for g in u2_groups]
        print(f"--> User 2 list_groups result: {u2_group_names}")
        assert "demo group" in u2_group_names

        # Check visibility for User 1 (querying with User 1's workspace ws1)
        u1_groups = await list_groups(organization_id=org.id, workspace_id=ws1.id, current_user=user_1, db=db)
        u1_group_names = [g.name for g in u1_groups]
        print(f"--> EXPECTED TEST B PASS: User 1 list_groups result: {u1_group_names}")
        assert "demo group" in u1_group_names, "CRITICAL BUG: 'demo group' is not visible to User 1 after being added!"

        # TEST C: User 1 opens "demo group"
        details_u1 = await get_group_details(group_id, current_user=user_1, db=db)
        member_ids_u1 = [m.user_id for m in (details_u1.members or [])]
        print(f"--> TEST C: User 1 opened group details. Members found: {len(member_ids_u1)}")
        assert details_u1.name == "demo group"
        assert user_1.id in member_ids_u1
        assert user_2.id in member_ids_u1

        # User 1 sends a message
        msg_1_payload = MessageCreatePayload(
            conversation_id=group_id,
            content="Hello from User 1 in demo group!",
            message_type="text",
            client_msg_id=f"u1-msg-{uuid4().hex[:8]}"
        )
        msg_1 = await send_message(msg_1_payload, current_user=user_1, db=db)
        print(f"--> User 1 sent message: '{msg_1.content}'")
        assert msg_1.content == "Hello from User 1 in demo group!"

        # TEST D: User 2 sends a message
        msg_2_payload = MessageCreatePayload(
            conversation_id=group_id,
            content="Hello User 1! Welcome to demo group.",
            message_type="text",
            client_msg_id=f"u2-msg-{uuid4().hex[:8]}"
        )
        msg_2 = await send_message(msg_2_payload, current_user=user_2, db=db)
        print(f"--> TEST D: User 2 sent message: '{msg_2.content}'")

        # User 1 checks message history
        history = await get_messages_history(group_id, limit=50, offset=0, current_user=user_1, db=db)
        print(f"--> User 1 history count: {len(history)} messages.")
        assert len(history) == 2
        assert history[1].content == "Hello User 1! Welcome to demo group."

        # User 1 marks conversation as read
        read_resp = await mark_conversation_as_read(group_id, current_user=user_1, db=db)
        print(f"--> User 1 marked conversation read: {read_resp}")
        assert read_resp["status"] == "success"

        # TEST E: Refresh User 1 query simulation (re-fetch list_groups)
        u1_refreshed_groups = await list_groups(organization_id=org.id, workspace_id=ws1.id, current_user=user_1, db=db)
        refreshed_names = [g.name for g in u1_refreshed_groups]
        print(f"--> TEST E: Refresh User 1 query result: {refreshed_names}")
        assert "demo group" in refreshed_names

        # Verify last_message preview & timestamp
        target_group = next(g for g in u1_refreshed_groups if g.name == "demo group")
        print(f"--> Verified last_message preview: '{target_group.last_message.content}' at {target_group.last_message_at}")
        assert target_group.last_message is not None
        assert target_group.last_message.content == "Hello User 1! Welcome to demo group."

        # TEST F: User 1 log out and log in simulation (fresh session query)
        u1_relogin_groups = await list_groups(organization_id=org.id, workspace_id=None, current_user=user_1, db=db)
        relogin_names = [g.name for g in u1_relogin_groups]
        print(f"--> TEST F: Relogin User 1 query result: {relogin_names}")
        assert "demo group" in relogin_names

        print("=== Phase 1.3 Group Visibility Integration Tests Passed 100%! ===")

if __name__ == "__main__":
    asyncio.run(run_group_visibility_tests())
