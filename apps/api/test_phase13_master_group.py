import asyncio
import os
import sys
from uuid import uuid4
from datetime import datetime
from fastapi import HTTPException

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
    add_group_member, AddMemberPayload,
    remove_group_member
)
from app.conversations.messages_router import send_message, MessageCreatePayload, get_messages_history
from app.conversations.router import mark_conversation_as_read

async def run_master_phase13_tests():
    print("==================================================")
    print("   MINDMESH PHASE 1.3 MASTER END-TO-END VERIFICATION")
    print("==================================================")
    
    async with AsyncSessionLocal() as db:
        suffix = uuid4().hex[:6]
        
        # 1. Setup Accounts
        user_a = User(
            id=uuid4(),
            email=f"usera_{suffix}@mindmesh.test",
            username=f"usera_{suffix}",
            hashed_password="test_hashed_password",
            first_name="Alice",
            last_name="Owner",
            is_active=True
        )
        user_b = User(
            id=uuid4(),
            email=f"userb_{suffix}@mindmesh.test",
            username=f"userb_{suffix}",
            hashed_password="test_hashed_password",
            first_name="Bob",
            last_name="Member",
            is_active=True
        )
        user_c_other_org = User(
            id=uuid4(),
            email=f"userc_other_{suffix}@mindmesh.test",
            username=f"userc_other_{suffix}",
            hashed_password="test_hashed_password",
            first_name="Charlie",
            last_name="Outsider",
            is_active=True
        )
        db.add_all([user_a, user_b, user_c_other_org])
        await db.flush()

        # Primary Org & Workspaces
        org_a = Organization(id=uuid4(), name=f"Primary Org {suffix}", slug=f"org-a-{suffix}", created_by=str(user_a.id))
        org_b = Organization(id=uuid4(), name=f"Other Org {suffix}", slug=f"org-b-{suffix}", created_by=str(user_c_other_org.id))
        db.add_all([org_a, org_b])
        await db.flush()

        ws_a1 = Workspace(id=uuid4(), organization_id=org_a.id, name="Eng Workspace A", slug=f"ws-a1-{suffix}")
        ws_a2 = Workspace(id=uuid4(), organization_id=org_a.id, name="Product Workspace B", slug=f"ws-a2-{suffix}")
        db.add_all([ws_a1, ws_a2])

        om_a = OrganizationMember(id=uuid4(), organization_id=org_a.id, user_id=user_a.id, role="owner")
        om_b = OrganizationMember(id=uuid4(), organization_id=org_a.id, user_id=user_b.id, role="member")
        om_c = OrganizationMember(id=uuid4(), organization_id=org_b.id, user_id=user_c_other_org.id, role="owner")
        db.add_all([om_a, om_b, om_c])
        await db.commit()

        print("--> Created 3 test users across 2 Organizations.")

        # TEST 1 — CREATE
        payload_1 = GroupCreatePayload(
            name="Engineering Team",
            description="Core infrastructure engineering group",
            organization_id=org_a.id,
            workspace_id=ws_a1.id,
            visibility="private",
            member_user_ids=[]
        )
        group_res_1 = await create_group(payload_1, current_user=user_a, db=db)
        group_id = group_res_1.id
        print(f"[PASS] TEST 1 (CREATE): User A created group '{group_res_1.name}' (ID: {group_id})")
        assert group_res_1.name == "Engineering Team"

        # TEST 2 — ADD MEMBER
        add_res_2 = await add_group_member(group_id, AddMemberPayload(user_id=user_b.id, role="member"), current_user=user_a, db=db)
        print(f"[PASS] TEST 2 (ADD MEMBER): User A added User B to Engineering Team. Member ID: {add_res_2.id}")
        assert add_res_2.user_id == user_b.id

        # TEST 3 — GROUP LIST
        u_b_groups = await list_groups(organization_id=org_a.id, workspace_id=ws_a2.id, current_user=user_b, db=db)
        u_b_names = [g.name for g in u_b_groups]
        print(f"[PASS] TEST 3 (GROUP LIST): User B list_groups result: {u_b_names}")
        assert "Engineering Team" in u_b_names

        # TEST 4 — OPEN
        details_b = await get_group_details(group_id, current_user=user_b, db=db)
        member_ids_b = [m.user_id for m in (details_b.members or [])]
        print(f"[PASS] TEST 4 (OPEN): User B opened details. Total members: {details_b.member_count}")
        assert details_b.name == "Engineering Team"
        assert user_a.id in member_ids_b
        assert user_b.id in member_ids_b

        # TEST 5 — SEND
        msg_b_payload = MessageCreatePayload(
            conversation_id=group_id,
            content="Hello User A",
            message_type="text",
            client_msg_id=f"msg-b1-{uuid4().hex[:8]}"
        )
        sent_b = await send_message(msg_b_payload, current_user=user_b, db=db)
        print(f"[PASS] TEST 5 (SEND): User B sent: '{sent_b.content}' (Status: {sent_b.status})")
        assert sent_b.content == "Hello User A"

        # TEST 6 — REPLY
        msg_a_payload = MessageCreatePayload(
            conversation_id=group_id,
            content="Hello User B",
            message_type="text",
            client_msg_id=f"msg-a1-{uuid4().hex[:8]}"
        )
        sent_a = await send_message(msg_a_payload, current_user=user_a, db=db)
        print(f"[PASS] TEST 6 (REPLY): User A replied: '{sent_a.content}' (Status: {sent_a.status})")
        assert sent_a.content == "Hello User B"

        # TEST 7 — REFRESH
        history_b = await get_messages_history(group_id, limit=50, offset=0, current_user=user_b, db=db)
        print(f"[PASS] TEST 7 (REFRESH): User B history retrieval count: {len(history_b)}")
        assert len(history_b) == 2
        assert history_b[0].content == "Hello User A"
        assert history_b[1].content == "Hello User B"

        # TEST 8 — LOGOUT / RELOGIN
        groups_b_relogin = await list_groups(organization_id=org_a.id, workspace_id=None, current_user=user_b, db=db)
        relogin_names = [g.name for g in groups_b_relogin]
        print(f"[PASS] TEST 8 (LOGOUT/RELOGIN): User B fresh login groups: {relogin_names}")
        assert "Engineering Team" in relogin_names

        # TEST 9 — UNREAD COUNTS
        msg_a_unread_payload = MessageCreatePayload(
            conversation_id=group_id,
            content="User B, please review the design doc when you are online.",
            message_type="text",
            client_msg_id=f"msg-unread-{uuid4().hex[:8]}"
        )
        await send_message(msg_a_unread_payload, current_user=user_a, db=db)
        
        # User B queries list_groups while outside the group
        b_groups_outside = await list_groups(organization_id=org_a.id, workspace_id=ws_a2.id, current_user=user_b, db=db)
        target_group = next(g for g in b_groups_outside if g.name == "Engineering Team")
        print(f"[PASS] TEST 9 (UNREAD): User B outside group unread_count = {target_group.unread_count}")
        assert target_group.unread_count >= 1

        # TEST 10 — READ STATE
        read_res = await mark_conversation_as_read(group_id, current_user=user_b, db=db)
        print(f"[PASS] TEST 10 (READ): User B opened group and marked read: {read_res}")
        
        b_groups_after_read = await list_groups(organization_id=org_a.id, workspace_id=ws_a2.id, current_user=user_b, db=db)
        target_group_read = next(g for g in b_groups_after_read if g.name == "Engineering Team")
        print(f"--> User B unread_count after reading = {target_group_read.unread_count}")
        assert target_group_read.unread_count == 0

        # TEST 11 — SECURITY & ISOLATION
        try:
            await get_group_details(group_id, current_user=user_c_other_org, db=db)
            security_passed = False
        except HTTPException as exc:
            print(f"[PASS] TEST 11 (SECURITY): Outsider User C access rejected with status {exc.status_code}: {exc.detail}")
            security_passed = (exc.status_code == 403 or exc.status_code == 404)
        assert security_passed

        # TEST 12 — MEMBER REMOVAL
        remove_res = await remove_group_member(group_id, user_b.id, current_user=user_a, db=db)
        print(f"[PASS] TEST 12 (MEMBER REMOVAL): User A removed User B. Message: {remove_res['message']}")
        
        try:
            await get_group_details(group_id, current_user=user_b, db=db)
            removal_verified = False
        except HTTPException as exc:
            removal_verified = (exc.status_code == 403 or exc.status_code == 404)
            print(f"--> User B access denied after removal with status {exc.status_code}")
        assert removal_verified

        print("==================================================")
        print("  ALL 12 MASTER ACCEPTANCE TESTS PASSED 100%!")
        print("==================================================")

if __name__ == "__main__":
    asyncio.run(run_master_phase13_tests())
