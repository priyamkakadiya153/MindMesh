import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.database.session import AsyncSessionLocal
from app.models.user import User
from sqlalchemy import select

async def inspect_orgs():
    async with AsyncSessionLocal() as db:
        u1 = (await db.execute(select(User).where(User.email == "testuser@mindmesh.com"))).scalar_one()
        u2 = (await db.execute(select(User).where(User.email == "test2@mindmesh.com"))).scalar_one()

        print(f"User 1 ({u1.email}): current_organization_id = {u1.current_organization_id}")
        print(f"User 2 ({u2.email}): current_organization_id = {u2.current_organization_id}")

if __name__ == "__main__":
    asyncio.run(inspect_orgs())
