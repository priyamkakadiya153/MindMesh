import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.database.session import AsyncSessionLocal
from app.models.user import User
from app.models.organization import Organization
from app.models.organization_member import OrganizationMember
from sqlalchemy import select

async def inspect_orgs():
    async with AsyncSessionLocal() as db:
        res1 = await db.execute(select(User).where(User.email == "testuser@mindmesh.com"))
        u1 = res1.scalar_one_or_none()
        
        res2 = await db.execute(select(User).where(User.email == "test2@mindmesh.com"))
        u2 = res2.scalar_one_or_none()

        print("=== USER 1 ===")
        print(f"ID: {u1.id if u1 else None}, Email: {u1.email if u1 else None}")
        if u1:
            om_res1 = await db.execute(select(OrganizationMember).where(OrganizationMember.user_id == u1.id))
            for om in om_res1.scalars().all():
                org = await db.get(Organization, om.organization_id)
                print(f"  - Org ID: {om.organization_id}, Name: {org.name if org else 'Unknown'}, Role: {om.role}")

        print("\n=== USER 2 ===")
        print(f"ID: {u2.id if u2 else None}, Email: {u2.email if u2 else None}")
        if u2:
            om_res2 = await db.execute(select(OrganizationMember).where(OrganizationMember.user_id == u2.id))
            for om in om_res2.scalars().all():
                org = await db.get(Organization, om.organization_id)
                print(f"  - Org ID: {om.organization_id}, Name: {org.name if org else 'Unknown'}, Role: {om.role}")

if __name__ == "__main__":
    asyncio.run(inspect_orgs())
