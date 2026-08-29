import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.database.session import AsyncSessionLocal
from app.models.user import User
from app.models.organization import Organization
from app.models.organization_member import OrganizationMember
from app.models.conversations import Conversation, ConversationMember
from app.conversations.groups_router import list_groups, create_group, GroupCreatePayload
from app.conversations.router import list_conversations
from sqlalchemy import select

async def run_credentials_test():
    print("==================================================")
    print("  CREDENTIALS AUDIT FOR testuser & test2")
    print("==================================================")

    async with AsyncSessionLocal() as db:
        # 1. Fetch user 1
        res1 = await db.execute(select(User).where(User.email == "testuser@mindmesh.com"))
        u1 = res1.scalar_one_or_none()
        
        # 2. Fetch user 2
        res2 = await db.execute(select(User).where(User.email == "test2@mindmesh.com"))
        u2 = res2.scalar_one_or_none()

        print(f"User 1: {u1.id if u1 else 'NOT FOUND'} ({u1.email if u1 else ''})")
        print(f"User 2: {u2.id if u2 else 'NOT FOUND'} ({u2.email if u2 else ''})")

        if not u1 or not u2:
            print("One of the test users does not exist in DB!")
            return

        # Check Organization Memberships for User 1 and User 2
        om1_res = await db.execute(select(OrganizationMember).where(OrganizationMember.user_id == u1.id))
        om1_list = om1_res.scalars().all()
        print(f"User 1 Org Memberships: {[(om.organization_id, om.role) for om in om1_list]}")

        om2_res = await db.execute(select(OrganizationMember).where(OrganizationMember.user_id == u2.id))
        om2_list = om2_res.scalars().all()
        print(f"User 2 Org Memberships: {[(om.organization_id, om.role) for om in om2_list]}")

        # Check existing conversations / groups in DB
        cm1_res = await db.execute(select(ConversationMember).where(ConversationMember.user_id == u1.id))
        cm1_list = cm1_res.scalars().all()
        conv_ids_1 = [cm.conversation_id for cm in cm1_list]
        print(f"User 1 Joined Conversations count: {len(conv_ids_1)}")

        cm2_res = await db.execute(select(ConversationMember).where(ConversationMember.user_id == u2.id))
        cm2_list = cm2_res.scalars().all()
        conv_ids_2 = [cm.conversation_id for cm in cm2_list]
        print(f"User 2 Joined Conversations count: {len(conv_ids_2)}")

        # Print all groups owned or joined by User 1
        if om1_list:
            org_id = om1_list[0].organization_id
            print(f"\n--- Querying list_groups for User 1 under Org {org_id} ---")
            groups_u1 = await list_groups(organization_id=org_id, current_user=u1, db=db)
            print(f"User 1 groups list: {[g.name for g in groups_u1]}")

            print(f"\n--- Querying list_groups for User 2 under Org {org_id} ---")
            groups_u2 = await list_groups(organization_id=org_id, current_user=u2, db=db)
            print(f"User 2 groups list: {[g.name for g in groups_u2]}")

if __name__ == "__main__":
    asyncio.run(run_credentials_test())
