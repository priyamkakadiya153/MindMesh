import pytest
from uuid import uuid4
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.organizations.service import OrganizationService
from app.organizations.schemas import OrgCreate
from app.workspace.service import WorkspaceService
from app.projects.service import ProjectService

@pytest.mark.asyncio
async def test_project_crud_and_settings(db_session: AsyncSession):
    user = User(
        email=f"proj_owner_{uuid4().hex[:6]}@example.com",
        username=f"proj_owner_{uuid4().hex[:6]}",
        hashed_password="hashed_password"
    )
    db_session.add(user)
    await db_session.commit()

    org_service = OrganizationService()
    org = await org_service.create_organization(
        db_session, user.id, OrgCreate(name="Project Org", slug=f"proj-org-{uuid4().hex[:4]}")
    )

    ws_service = WorkspaceService(db_session)
    ws = await ws_service.create_workspace(
        name="Dev Workspace", org_id=org.id, user_id=user.id
    )

    proj_service = ProjectService(db_session)
    proj = await proj_service.create_project(
        name="Knowledge Graph System",
        workspace_id=ws.id,
        org_id=org.id,
        user_id=user.id,
        description="Graph-based semantic memory engine",
        color="#8B5CF6",
        status_val="planning"
    )

    assert proj.name == "Knowledge Graph System"
    assert proj.status == "planning"
    assert proj.workspace_id == ws.id
    assert proj.organization_id == org.id

    # Verify Auto Settings
    settings = await proj_service.get_settings(proj.id, org.id)
    assert settings is not None
    assert settings.enable_ai is True

    # Update Settings
    updated_settings = await proj_service.update_settings(proj.id, org.id, enable_ai=False, notification_level="mentions")
    assert updated_settings.enable_ai is False
    assert updated_settings.notification_level == "mentions"

@pytest.mark.asyncio
async def test_project_search_and_filtering(db_session: AsyncSession):
    user = User(
        email=f"search_user_{uuid4().hex[:6]}@example.com",
        username=f"search_user_{uuid4().hex[:6]}",
        hashed_password="hashed_password"
    )
    db_session.add(user)
    await db_session.commit()

    org_service = OrganizationService()
    org = await org_service.create_organization(
        db_session, user.id, OrgCreate(name="Filter Org", slug=f"filter-org-{uuid4().hex[:4]}")
    )

    ws_service = WorkspaceService(db_session)
    ws = await ws_service.create_workspace(
        name="Search Workspace", org_id=org.id, user_id=user.id
    )

    proj_service = ProjectService(db_session)
    p1 = await proj_service.create_project(
        name="Alpha Service", workspace_id=ws.id, org_id=org.id, user_id=user.id, status_val="active"
    )
    p2 = await proj_service.create_project(
        name="Beta Pipeline", workspace_id=ws.id, org_id=org.id, user_id=user.id, status_val="planning"
    )
    p3 = await proj_service.create_project(
        name="Gamma Analytics", workspace_id=ws.id, org_id=org.id, user_id=user.id, status_val="completed"
    )

    # Search filter
    alpha_projects = await proj_service.list_projects(org.id, workspace_id=ws.id, search="Alpha")
    assert len(alpha_projects) == 1
    assert alpha_projects[0].name == "Alpha Service"

    # Status filter
    planning_projects = await proj_service.list_projects(org.id, workspace_id=ws.id, status_val="planning")
    assert len(planning_projects) == 1
    assert planning_projects[0].name == "Beta Pipeline"

@pytest.mark.asyncio
async def test_project_archiving_and_restoration(db_session: AsyncSession):
    user = User(
        email=f"archive_user_{uuid4().hex[:6]}@example.com",
        username=f"archive_user_{uuid4().hex[:6]}",
        hashed_password="hashed_password"
    )
    db_session.add(user)
    await db_session.commit()

    org_service = OrganizationService()
    org = await org_service.create_organization(
        db_session, user.id, OrgCreate(name="Archive Org", slug=f"arch-org-{uuid4().hex[:4]}")
    )

    ws_service = WorkspaceService(db_session)
    ws = await ws_service.create_workspace(
        name="Archive Workspace", org_id=org.id, user_id=user.id
    )

    proj_service = ProjectService(db_session)
    proj = await proj_service.create_project(
        name="Legacy System Migration", workspace_id=ws.id, org_id=org.id, user_id=user.id
    )

    # Archive
    archived_proj = await proj_service.archive_project(proj.id, org.id)
    assert archived_proj.is_archived is True
    assert archived_proj.status == "archived"

    # Restore
    restored_proj = await proj_service.restore_project(proj.id, org.id)
    assert restored_proj.is_archived is False
    assert restored_proj.status == "active"

@pytest.mark.asyncio
async def test_project_member_management(db_session: AsyncSession):
    owner = User(
        email=f"owner_{uuid4().hex[:6]}@example.com",
        username=f"owner_{uuid4().hex[:6]}",
        hashed_password="hashed_password"
    )
    member_user = User(
        email=f"contributor_{uuid4().hex[:6]}@example.com",
        username=f"contributor_{uuid4().hex[:6]}",
        hashed_password="hashed_password"
    )
    db_session.add_all([owner, member_user])
    await db_session.commit()

    org_service = OrganizationService()
    org = await org_service.create_organization(
        db_session, owner.id, OrgCreate(name="Member Org", slug=f"mem-org-{uuid4().hex[:4]}")
    )

    ws_service = WorkspaceService(db_session)
    ws = await ws_service.create_workspace(
        name="Member Workspace", org_id=org.id, user_id=owner.id
    )

    proj_service = ProjectService(db_session)
    proj = await proj_service.create_project(
        name="Team Collaboration Project", workspace_id=ws.id, org_id=org.id, user_id=owner.id
    )

    # Add member
    mem = await proj_service.add_project_member(proj.id, org.id, member_user.email, "contributor")
    assert mem.user_id == member_user.id
    assert mem.role == "contributor"

    # Update role to manager
    updated_mem = await proj_service.update_project_member(proj.id, org.id, member_user.id, role="manager")
    assert updated_mem.role == "manager"

    # List members
    members = await proj_service.get_project_members(proj.id, org.id)
    emails = [m["email"] for m in members]
    assert member_user.email in emails

    # Remove member
    await proj_service.remove_project_member(proj.id, org.id, member_user.id)
    members_after = await proj_service.get_project_members(proj.id, org.id)
    assert member_user.email not in [m["email"] for m in members_after]

@pytest.mark.asyncio
async def test_project_dashboard_overview(db_session: AsyncSession):
    user = User(
        email=f"dash_user_{uuid4().hex[:6]}@example.com",
        username=f"dash_user_{uuid4().hex[:6]}",
        hashed_password="hashed_password"
    )
    db_session.add(user)
    await db_session.commit()

    org_service = OrganizationService()
    org = await org_service.create_organization(
        db_session, user.id, OrgCreate(name="Dash Org", slug=f"dash-org-{uuid4().hex[:4]}")
    )

    ws_service = WorkspaceService(db_session)
    ws = await ws_service.create_workspace(
        name="Dash Workspace", org_id=org.id, user_id=user.id
    )

    proj_service = ProjectService(db_session)
    proj = await proj_service.create_project(
        name="Analytics Dashboard", workspace_id=ws.id, org_id=org.id, user_id=user.id
    )

    dashboard = await proj_service.get_dashboard(proj.id, org.id)
    assert dashboard["project"].id == proj.id
    assert dashboard["member_count"] >= 1
    assert "recent_activity" in dashboard
