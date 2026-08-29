import asyncio
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from ..core.database import AsyncSessionLocal
from ..models.user import User
from ..models.organization import Organization
from ..models.organization_member import OrganizationMember
from ..workspace.models import Workspace, WorkspaceMember

async def seed_workspace_data(session: AsyncSession):
    stmt = select(User).where(User.email == "admin@mindmesh.com")
    res = await session.execute(stmt)
    admin = res.scalar_one_or_none()
    if not admin:
        print("[Seed Workspace] Admin user not found. Run main seed first.")
        return

    stmt = select(Organization).limit(1)
    res = await session.execute(stmt)
    org = res.scalar_one_or_none()
    if not org:
        print("[Seed Workspace] Organization not found. Run main seed first.")
        return

    stmt = select(Workspace).where(Workspace.slug == "engineering", Workspace.organization_id == org.id)
    res = await session.execute(stmt)
    existing = res.scalar_one_or_none()
    if existing:
        print("[Seed Workspace] Engineering workspace already exists. Skipping.")
        return

    print("[Seed Workspace] Creating engineering workspace...")
    workspace = Workspace(
        name="Engineering",
        slug="engineering",
        organization_id=org.id,
        description="Core engineering workspace",
        icon="cpu",
        color="#3B82F6",
        is_default=True,
        is_archived=False,
        created_by=admin.id
    )
    session.add(workspace)
    await session.flush()

    print("[Seed Workspace] Creating workspace membership for admin...")
    ws_member = WorkspaceMember(
        workspace_id=workspace.id,
        user_id=admin.id,
        role="OWNER"
    )
    session.add(ws_member)
    print("[Seed Workspace] Seeding workspace completed successfully.")

async def main():
    async with AsyncSessionLocal() as session:
        await seed_workspace_data(session)
        await session.commit()

if __name__ == "__main__":
    asyncio.run(main())
