import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.database.session import AsyncSessionLocal
from app.models.user import User
from app.conversations.groups_router import list_groups, create_group, GroupCreatePayload
from sqlalchemy import select

async def run_shared_org_test():
    shared_org_id = "6d6e2185-325d-4745-9bf0-d2e68a4a6fb7" # testuser2's Personal Org
    
    async with AsyncSessionLocal() as db:
        res1 = await db.execute(select(User).where(User.email == "testuser@mindmesh.com"))
        u1 = res1.scalar_one_or_none()
        
        res2 = await db.execute(select(User).where(User.email == "test2@mindmesh.com"))
        u2 = res2.scalar_one_or_none()

        print(f"Testing in Shared Org {shared_org_id} ('testuser2 Personal Org')...")

        # 1. Create a group in Shared Org by User 1 with User 2 as member
        create_payload = GroupCreatePayload(
            name="Shared Org Group",
            description="Testing group in shared organization",
            organization_id=shared_org_id,
            visibility="private",
            member_user_ids=[str(u2.id)]
        )
        group_res = await create_group(create_payload, current_user=u1, db=db)
        print(f"Created group: '{group_res.name}' (ID: {group_res.id}) under Org {shared_org_id}")

        # 2. Query list_groups for User 1
        groups_1 = await list_groups(organization_id=shared_org_id, current_user=u1, db=db)
        print(f"User 1 list_groups count: {len(groups_1)}, names: {[g.name for g in groups_1]}")

        # 3. Query list_groups for User 2
        groups_2 = await list_groups(organization_id=shared_org_id, current_user=u2, db=db)
        print(f"User 2 list_groups count: {len(groups_2)}, names: {[g.name for g in groups_2]}")

if __name__ == "__main__":
    asyncio.run(run_shared_org_test())
