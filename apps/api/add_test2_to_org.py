import asyncio
import os
import sys
from uuid import uuid4

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.database.session import AsyncSessionLocal
from app.models.user import User
from app.models.organization_member import OrganizationMember
from sqlalchemy import select

async def add_memberships():
    async with AsyncSessionLocal() as db:
        u1_res = await db.execute(select(User).where(User.email == "testuser@mindmesh.com"))
        u1 = u1_res.scalar_one_or_none()

        u2_res = await db.execute(select(User).where(User.email == "test2@mindmesh.com"))
        u2 = u2_res.scalar_one_or_none()

        if not u1 or not u2:
            print("Users not found")
            return

        # Ensure u1 and u2 are members of all 3 orgs
        org_ids = [
            "e71290e6-e228-475a-9132-f256fd099973", # testuser's Personal Org
            "92b86602-7cae-481b-9c8f-7a6378d98b9b", # kakadiya's Personal Org
            "6d6e2185-325d-4745-9bf0-d2e68a4a6fb7"  # testuser2's Personal Org
        ]

        for org_id in org_ids:
            for u in [u1, u2]:
                m_stmt = select(OrganizationMember).where(
                    OrganizationMember.organization_id == org_id,
                    OrganizationMember.user_id == u.id
                )
                m_res = await db.execute(m_stmt)
                if not m_res.scalar_one_or_none():
                    db.add(OrganizationMember(
                        id=uuid4(),
                        organization_id=org_id,
                        user_id=u.id,
                        role="member"
                    ))
                    print(f"Added user {u.email} to Org {org_id}")

        await db.commit()
        print("Organization memberships updated successfully!")

if __name__ == "__main__":
    asyncio.run(add_memberships())
