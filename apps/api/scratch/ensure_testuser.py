import sys, os
sys.path.insert(0, os.path.abspath("."))
import asyncio
from app.documents.models import Document
import app.models  # Load all models for mapper registry
from sqlalchemy import select
from app.core.database import AsyncSessionLocal
from app.models.user import User
from app.models.organization import Organization
from app.models.organization_member import OrganizationMember
from app.models.workspace import Workspace
from app.models.workspace_member import WorkspaceMember
from app.core.security import get_password_hash
from uuid import uuid4

async def main():
    session = AsyncSessionLocal()
    res = await session.execute(select(User).where(User.email == 'testuser@mindmesh.com'))
    user = res.scalar_one_or_none()
    
    if not user:
        print("User testuser@mindmesh.com does not exist. Creating...")
        res_org = await session.execute(select(Organization).limit(1))
        org = res_org.scalar_one_or_none()
        if not org:
            org = Organization(id=uuid4(), name="MindMesh Corp", slug="mindmesh-corp")
            session.add(org)
            await session.commit()
            
        res_ws = await session.execute(select(Workspace).where(Workspace.organization_id == org.id).limit(1))
        ws = res_ws.scalar_one_or_none()
        if not ws:
            ws = Workspace(id=uuid4(), organization_id=org.id, name="Primary Workspace", slug="primary-workspace")
            session.add(ws)
            await session.commit()
            
        hashed = get_password_hash("Password123!")
        user = User(
            id=uuid4(),
            email="testuser@mindmesh.com",
            username="testuser",
            hashed_password=hashed,
            is_verified=True,
            current_organization_id=org.id,
            current_workspace_id=ws.id
        )
        session.add(user)
        await session.commit()

        org_member = OrganizationMember(id=uuid4(), organization_id=org.id, user_id=user.id, role="owner", status="active")
        session.add(org_member)
        ws_member = WorkspaceMember(id=uuid4(), workspace_id=ws.id, user_id=user.id, role="owner", status="active")
        session.add(ws_member)
        await session.commit()
        print("User testuser@mindmesh.com created successfully with Password123!")
    else:
        user.hashed_password = get_password_hash("Password123!")
        await session.commit()
        print("User testuser@mindmesh.com password updated to Password123!")
        
    await session.close()

if __name__ == "__main__":
    asyncio.run(main())
