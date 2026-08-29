import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.database.session import AsyncSessionLocal
from app.models.user import User
from app.conversations.groups_router import list_groups, create_group, GroupCreatePayload
from sqlalchemy import select

async def test_live_flow():
    async with AsyncSessionLocal() as db:
        u1 = (await db.execute(select(User).where(User.email == "testuser@mindmesh.com"))).scalar_one()
        u2 = (await db.execute(select(User).where(User.email == "test2@mindmesh.com"))).scalar_one()

        print("=== LIVE CREDENTIALS FLOW TEST ===")
        print(f"Creating group by testuser ({u1.email}) adding testuser2 ({u2.email})...")

        payload = GroupCreatePayload(
            name="Live Browser Test Group",
            description="Testing manual group creation with user credentials",
            organization_id=u1.current_organization_id or "e71290e6-e228-475a-9132-f256fd099973",
            visibility="private",
            member_user_ids=[str(u2.id)]
        )

        group = await create_group(payload, current_user=u1, db=db)
        print(f"[PASS] Group created: '{group.name}' (ID: {group.id}) under Org {payload.organization_id}")

        # Query list_groups for test2@mindmesh.com under payload.organization_id
        g2 = await list_groups(organization_id=payload.organization_id, current_user=u2, db=db)
        g2_names = [g.name for g in g2]
        print(f"[PASS] test2@mindmesh.com list_groups result: {g2_names}")

        assert "Live Browser Test Group" in g2_names
        print("==================================================")
        print(" [SUCCESS] test2@mindmesh.com SEES THE NEW GROUP!")
        print("==================================================")

if __name__ == "__main__":
    asyncio.run(test_live_flow())
