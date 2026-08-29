import asyncio
import os
import sys
from uuid import uuid4
from datetime import datetime

# Add project root to sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select, delete, text

from app.database.session import AsyncSessionLocal
from app.models.user import User
from app.models.organization import Organization
from app.models.organization_member import OrganizationMember
from app.models.workspace import Workspace
from app.models.workspace_member import WorkspaceMember
from app.models.conversations import Conversation, ConversationMember, DirectMessage

from app.conversations.groups_router import (
    create_group, GroupCreatePayload,
    get_group_details,
    add_group_member, AddMemberPayload,
    remove_group_member,
    update_member_role, UpdateMemberRolePayload,
    toggle_archive_group
)
from app.conversations.messages_router import send_message, MessageCreatePayload, get_messages_history

async def run_group_tests():
    print("=== Starting MindMesh Group Messaging Tests ===")
    async with AsyncSessionLocal() as db:
        # 1. Setup test organization & 3 test users
        suffix = uuid4().hex[:6]
        user_a = User(
            id=uuid4(),
            email=f"group_admin_{suffix}@mindmesh.test",
            username=f"group_admin_{suffix}",
            hashed_password="hashed_pass_test",
            first_name="Alice",
            last_name="Owner",
            is_active=True
        )
        user_b = User(
            id=uuid4(),
            email=f"group_mem_b_{suffix}@mindmesh.test",
            username=f"group_mem_b_{suffix}",
            hashed_password="hashed_pass_test",
            first_name="Bob",
            last_name="Admin",
            is_active=True
        )
        user_c = User(
            id=uuid4(),
            email=f"group_mem_c_{suffix}@mindmesh.test",
            username=f"group_mem_c_{suffix}",
            hashed_password="hashed_pass_test",
            first_name="Charlie",
            last_name="Member",
            is_active=True
        )
        db.add_all([user_a, user_b, user_c])
        await db.flush()

        org = Organization(
            id=uuid4(),
            name=f"Group Test Org {suffix}",
            slug=f"group-org-{suffix}",
            created_by=str(user_a.id)
        )
        db.add(org)
        await db.flush()

        # Add all 3 users as org members
        om_a = OrganizationMember(id=uuid4(), organization_id=org.id, user_id=user_a.id, role="owner")
        om_b = OrganizationMember(id=uuid4(), organization_id=org.id, user_id=user_b.id, role="member")
        om_c = OrganizationMember(id=uuid4(), organization_id=org.id, user_id=user_c.id, role="member")
        db.add_all([om_a, om_b, om_c])
        await db.commit()

        print("--> Created test org and 3 test users.")

        # 2. User A creates Group "MindMesh Core Team" with User B
        payload = GroupCreatePayload(
            name="MindMesh Core Team",
            description="Engineering and product discussions",
            organization_id=org.id,
            visibility="private",
            member_user_ids=[user_b.id]
        )
        group_resp = await create_group(payload, current_user=user_a, db=db)
        group_id = group_resp.id
        print(f"--> User A created group '{group_resp.name}' (ID: {group_id}) with member_count = {group_resp.member_count}")
        assert group_resp.name == "MindMesh Core Team"
        assert group_resp.member_count == 2

        # 3. User A adds User C to group
        add_resp = await add_group_member(group_id, AddMemberPayload(user_id=user_c.id, role="member"), current_user=user_a, db=db)
        print(f"--> User A added User C ({add_resp.full_name}) to group.")
        assert add_resp.user_id == user_c.id

        # 4. User A promotes User B to "admin"
        role_resp = await update_member_role(group_id, user_b.id, UpdateMemberRolePayload(role="admin"), current_user=user_a, db=db)
        print(f"--> User A updated User B role: {role_resp['message']}")
        assert role_resp["status"] == "success"

        # 5. User B (now Admin) sends a message to the group
        msg_payload = MessageCreatePayload(
            conversation_id=group_id,
            content="Hello MindMesh Core Team! Excited to build together.",
            message_type="text",
            client_msg_id=f"group-msg-{uuid4().hex[:8]}"
        )
        sent_msg = await send_message(msg_payload, current_user=user_b, db=db)
        print(f"--> User B sent group message: '{sent_msg.content}' (Status: {sent_msg.status})")
        assert sent_msg.content == "Hello MindMesh Core Team! Excited to build together."

        # 6. User C retrieves group messages history
        history = await get_messages_history(group_id, limit=50, offset=0, current_user=user_c, db=db)
        print(f"--> User C retrieved group history: {len(history)} messages found.")
        assert len(history) >= 1
        assert history[0].content == "Hello MindMesh Core Team! Excited to build together."

        # 7. User C leaves the group
        leave_resp = await remove_group_member(group_id, user_c.id, current_user=user_c, db=db)
        print(f"--> User C left group: {leave_resp['message']}")
        assert leave_resp["status"] == "success"

        # 8. User A fetches updated group details
        updated_group = await get_group_details(group_id, current_user=user_a, db=db)
        print(f"--> Updated member count: {updated_group.member_count}")
        assert updated_group.member_count == 2

        # 9. User A archives the group
        archive_resp = await toggle_archive_group(group_id, current_user=user_a, db=db)
        print(f"--> User A archived group: is_archived = {archive_resp['is_archived']}")
        assert archive_resp["is_archived"] is True

        print("=== All MindMesh Group Messaging Tests Passed Successfully! ===")

if __name__ == "__main__":
    asyncio.run(run_group_tests())
