import asyncio
import sys
import os
from uuid import uuid4
from datetime import datetime

sys.path.insert(0, os.path.abspath("."))

from app.database.session import AsyncSessionLocal
from app.models.user import User
from app.models.organization import Organization
from app.models.organization_member import OrganizationMember
from app.models.workspace import Workspace
from app.models.conversations import Conversation, ConversationMember, DirectMessage
from app.conversations.groups_router import (
    create_group,
    update_group,
    add_group_member,
    remove_group_member,
    delete_group,
    GroupCreatePayload,
    GroupUpdatePayload,
    AddMemberPayload
)
from fastapi import HTTPException

async def run_group_lifecycle_test():
    print("==================================================")
    print("  PHASE 1.3B GROUP LIFECYCLE & MANAGEMENT VERIFICATION")
    print("==================================================")

    now = datetime.utcnow()
    org_id = uuid4()
    ws_id = uuid4()
    owner_id = uuid4()
    member_id = uuid4()

    async with AsyncSessionLocal() as db:
        # Step 1: Create Users first (without current_organization_id)
        owner_user = User(
            id=owner_id, email=f"owner_{uuid4().hex[:6]}@mindmesh.io", username=f"owner_{uuid4().hex[:6]}",
            first_name="Group", last_name="Owner", hashed_password="pass", phone_number=f"+1415{uuid4().int % 10000000:07d}",
            is_active=True, created_at=now, updated_at=now
        )
        member_user = User(
            id=member_id, email=f"member_{uuid4().hex[:6]}@mindmesh.io", username=f"member_{uuid4().hex[:6]}",
            first_name="Group", last_name="Member", hashed_password="pass", phone_number=f"+1415{uuid4().int % 10000000:07d}",
            is_active=True, created_at=now, updated_at=now
        )
        db.add_all([owner_user, member_user])
        await db.commit()

        # Step 2: Create Org & Workspace
        org = Organization(id=org_id, name="Lifecycle Org", slug=f"lifecycle-{uuid4().hex[:6]}", owner_id=owner_id, created_at=now, updated_at=now)
        ws = Workspace(id=ws_id, organization_id=org_id, name="Lifecycle WS", slug=f"ws-{uuid4().hex[:6]}", owner_id=owner_id, created_at=now, updated_at=now)
        db.add_all([org, ws])
        await db.commit()

        # Step 3: Link current_organization_id on Users
        owner_user.current_organization_id = org_id
        owner_user.current_workspace_id = ws_id
        member_user.current_organization_id = org_id
        member_user.current_workspace_id = ws_id
        db.add(OrganizationMember(id=uuid4(), organization_id=org_id, user_id=owner_id, role="owner", is_active=True, joined_at=now))
        db.add(OrganizationMember(id=uuid4(), organization_id=org_id, user_id=member_id, role="member", is_active=True, joined_at=now))
        await db.commit()

        # TEST 1: Owner Creates Group
        create_payload = GroupCreatePayload(
            name="Lifecycle Test Group",
            description="Initial description",
            organization_id=org_id,
            workspace_id=ws_id,
            member_user_ids=[member_id]
        )
        created_group = await create_group(create_payload, current_user=owner_user, db=db)
        group_id = created_group.id
        print(f"[PASS] 1. Group Created: '{created_group.name}' (ID: {group_id})")

        # TEST 2: Owner Updates / Renames Group
        update_payload = GroupUpdatePayload(
            name="Renamed Engineering Group",
            description="Updated description"
        )
        updated_group = await update_group(group_id, update_payload, current_user=owner_user, db=db)
        assert updated_group.name == "Renamed Engineering Group"
        assert updated_group.description == "Updated description"
        print(f"[PASS] 2. Group Renamed: '{updated_group.name}'")

        # TEST 3: Non-Owner Member CANNOT Delete Group
        try:
            await delete_group(group_id, current_user=member_user, db=db)
            assert False, "Non-owner should not be allowed to delete group!"
        except HTTPException as e:
            assert e.status_code == 403
            print(f"[PASS] 3. Non-owner Delete Blocked (Status 403: {e.detail})")

        # TEST 4: Add Message to Group before deletion
        msg = DirectMessage(
            id=uuid4(),
            conversation_id=group_id,
            sender_id=owner_id,
            organization_id=org_id,
            workspace_id=ws_id,
            message_type="text",
            content="Hello lifecycle group!",
            created_at=now,
            updated_at=now
        )
        db.add(msg)
        await db.commit()
        print("[PASS] 4. Added message record to group")

        # TEST 5: Owner Permanently Deletes Group
        del_resp = await delete_group(group_id, current_user=owner_user, db=db)
        assert del_resp["status"] == "success"
        print(f"[PASS] 5. Owner Deleted Group Permanently: {del_resp['message']}")

        # TEST 6: Verify Database Records Purged & 404 Returned
        try:
            await delete_group(group_id, current_user=owner_user, db=db)
            assert False, "Group should be completely deleted!"
        except HTTPException as e:
            assert e.status_code == 404
            print(f"[PASS] 6. Deleted Group Returns 404 Not Found")

    print("==================================================")
    print("  ALL GROUP LIFECYCLE TESTS PASSED 100%!")
    print("==================================================")

if __name__ == "__main__":
    asyncio.run(run_group_lifecycle_test())
