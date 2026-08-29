import asyncio
import sys
import os
from uuid import uuid4

sys.path.insert(0, os.path.abspath("."))

from app.core.database import AsyncSessionLocal
from app.models.user import User
from app.models.organization import Organization
from app.models.workspace import Workspace
from app.core.security import create_access_token
from sqlalchemy import select

async def main():
    async with AsyncSessionLocal() as db:
        res = await db.execute(select(User).limit(1))
        user = res.scalar_one_or_none()
        if not user:
            org_id = uuid4()
            user = User(
                id=uuid4(),
                email="admin@mindmesh.com",
                full_name="Admin User",
                current_organization_id=org_id
            )
            db.add(user)
            await db.commit()
            await db.refresh(user)

        tok = create_access_token(
            subject=str(user.id),
            org_id=str(user.current_organization_id or uuid4()),
            workspace_id=str(user.current_workspace_id or uuid4()),
            role="ADMIN"
        )
        print("TOKEN:" + tok)

if __name__ == "__main__":
    asyncio.run(main())
