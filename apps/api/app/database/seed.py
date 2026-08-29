import asyncio
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from ..core.database import AsyncSessionLocal
from ..models.user import User
from ..models.role import Role
from ..models.permission import Permission
from ..models.organization import Organization
from ..models.organization_member import OrganizationMember
from ..workspace.models import Workspace, WorkspaceMember
from ..projects.models import Project, ProjectMember
from ..models.audit import AuditLog

from passlib.hash import bcrypt


async def seed_data(session: AsyncSession):
    permissions_list = [
        ("project.read", "Allows reading project data"),
        ("project.create", "Allows creating new projects"),
        ("project.update", "Allows modifying existing projects"),
        ("project.delete", "Allows deleting projects"),
        ("chat.read", "Allows reading chats"),
        ("chat.create", "Allows posting messages in chats"),
        ("document.upload", "Allows uploading files to knowledge base"),
        ("analytics.read", "Allows viewing analytics events"),
        ("admin.manage", "Full administrator access and configuration management")
    ]
    
    db_permissions = {}
    for name, desc in permissions_list:
        stmt = select(Permission).where(Permission.name == name)
        res = await session.execute(stmt)
        perm = res.scalar_one_or_none()
        if not perm:
            perm = Permission(name=name, description=desc)
            session.add(perm)
        db_permissions[name] = perm
    await session.flush()

    roles_permissions_map = {
        "SUPER_ADMIN": ["project.read", "project.create", "project.update", "project.delete", "chat.read", "chat.create", "document.upload", "analytics.read", "admin.manage"],
        "ORG_ADMIN": ["project.read", "project.create", "project.update", "chat.read", "chat.create", "document.upload", "analytics.read"],
        "PROJECT_MANAGER": ["project.read", "project.create", "project.update", "chat.read", "chat.create", "document.upload"],
        "MEMBER": ["project.read", "chat.read", "chat.create", "document.upload"],
        "GUEST": ["project.read", "chat.read"]
    }

    from sqlalchemy.orm import selectinload
    db_roles = {}
    for role_name, perm_names in roles_permissions_map.items():
        stmt = select(Role).options(selectinload(Role.permissions)).where(Role.name == role_name)
        res = await session.execute(stmt)
        role = res.scalar_one_or_none()
        if not role:
            role = Role(
                name=role_name,
                description=f"Default {role_name} Role",
                permissions=[db_permissions[p_name] for p_name in perm_names]
            )
            session.add(role)
            await session.flush()
        db_roles[role_name] = role
    await session.flush()

    admin_email = "admin@mindmesh.com"
    stmt = select(User).where(User.email == admin_email)
    res = await session.execute(stmt)
    admin = res.scalar_one_or_none()

    if not admin:
        print("[Seed] Creating system admin user...")
        admin = User(
            email=admin_email,
            username="admin",
            hashed_password=bcrypt.hash("adminpassword123"),
            phone_number="+1234567890",
            first_name="System",
            last_name="Administrator",
            is_verified=True,
        )
        session.add(admin)
        await session.flush()

    org_stmt = select(Organization).where(Organization.slug == "mindmesh-corp")
    org_res = await session.execute(org_stmt)
    org = org_res.scalars().first()
    if not org:
        print("[Seed] Creating default organization...")
        org = Organization(
            name="MindMesh Corporation",
            slug="mindmesh-corp",
            description="Default tenant organization container.",
            owner_id=admin.id
        )
        session.add(org)
        await session.flush()

    om_admin_stmt = select(OrganizationMember).where(OrganizationMember.organization_id == org.id, OrganizationMember.user_id == admin.id)
    om_admin_res = await session.execute(om_admin_stmt)
    if not om_admin_res.scalars().first():
        print("[Seed] Creating organization membership for admin...")
        member = OrganizationMember(
            organization_id=org.id,
            user_id=admin.id,
            role_id=db_roles["SUPER_ADMIN"].id
        )
        session.add(member)

    ws_stmt = select(Workspace).where(Workspace.slug == "primary-workspace")
    ws_res = await session.execute(ws_stmt)
    workspace = ws_res.scalars().first()
    if not workspace:
        print("[Seed] Creating default workspace...")
        workspace = Workspace(
            name="Primary Workspace",
            slug="primary-workspace",
            organization_id=org.id,
        )
        session.add(workspace)
        await session.flush()

        print("[Seed] Creating default sample project...")
        project = Project(
            name="Sample Project Alpha",
            slug="project-alpha",
            workspace_id=workspace.id,
            organization_id=org.id,
        )
        session.add(project)
        await session.flush()

        print("[Seed] Creating workspace membership for admin...")
        ws_member = WorkspaceMember(
            workspace_id=workspace.id,
            user_id=admin.id,
            role="OWNER"
        )
        session.add(ws_member)

        # Set initial current selection
        admin.current_organization_id = org.id
        admin.current_workspace_id = workspace.id


        print("[Seed] Creating project membership for admin...")
        proj_member = ProjectMember(
            project_id=project.id,
            user_id=admin.id,
            role="OWNER"
        )
        session.add(proj_member)

        print("[Seed] Creating initial audit log activity...")
        audit = AuditLog(
            action="Workspace Created",
            user_id=admin.id,
            organization_id=org.id,
            details={"workspace_name": workspace.name}
        )
        session.add(audit)

        print("[Seed] Seeding completed successfully.")

    # Query default organization and workspace
    default_org_stmt = select(Organization).where(Organization.slug == "mindmesh-corp")
    default_org_res = await session.execute(default_org_stmt)
    default_org = default_org_res.scalars().first()

    default_ws_stmt = select(Workspace).where(Workspace.slug == "primary-workspace")
    default_ws_res = await session.execute(default_ws_stmt)
    default_ws = default_ws_res.scalars().first()

    # Seed User 1 and User 2 for manual verification
    for phone_num, email_addr, u_name, f_name, l_name in [
        ("+919876543210", "user1@example.com", "user1", "User", "One"),
        ("+919988776655", "user2@example.com", "user2", "User", "Two")
    ]:
        u_stmt = select(User).where((User.email == email_addr) | (User.phone_number == phone_num))
        u_res = await session.execute(u_stmt)
        test_u = u_res.scalars().first()
        if not test_u:
            test_u = User(
                email=email_addr,
                username=u_name,
                hashed_password=bcrypt.hash("Password123!"),
                phone_number=phone_num,
                first_name=f_name,
                last_name=l_name,
                is_verified=True,
                is_phone_verified=True,
                current_organization_id=default_org.id if default_org else None,
                current_workspace_id=default_ws.id if default_ws else None
            )
            session.add(test_u)
            await session.flush()
            print(f"[Seed] Created verification user: {email_addr} ({phone_num})")
        else:
            if default_org and not test_u.current_organization_id:
                test_u.current_organization_id = default_org.id
            if default_ws and not test_u.current_workspace_id:
                test_u.current_workspace_id = default_ws.id

        if default_org:
            om_stmt = select(OrganizationMember).where(
                OrganizationMember.organization_id == default_org.id,
                OrganizationMember.user_id == test_u.id
            )
            om_res = await session.execute(om_stmt)
            if not om_res.scalars().first():
                session.add(OrganizationMember(
                    organization_id=default_org.id,
                    user_id=test_u.id,
                    role_id=db_roles["MEMBER"].id if "MEMBER" in db_roles else None
                ))

        if default_ws:
            wm_stmt = select(WorkspaceMember).where(
                WorkspaceMember.workspace_id == default_ws.id,
                WorkspaceMember.user_id == test_u.id
            )
            wm_res = await session.execute(wm_stmt)
            if not wm_res.scalars().first():
                session.add(WorkspaceMember(
                    workspace_id=default_ws.id,
                    user_id=test_u.id,
                    role="MEMBER"
                ))

    await session.flush()


async def run_seed():
    async with AsyncSessionLocal() as session:
        await seed_data(session)
        await session.commit()

if __name__ == "__main__":
    asyncio.run(run_seed())
