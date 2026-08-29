import pytest
from uuid import uuid4
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.organizations.service import OrganizationService
from app.organizations.schemas import OrgCreate
from app.workspace.service import WorkspaceService
from app.projects.service import ProjectService
from app.dashboard.service import DashboardService
from app.activity.service import ActivityService
from app.search.service import SearchService

@pytest.mark.asyncio
async def test_dashboard_overview_metrics(db_session: AsyncSession):
    user = User(
        email=f"dash_owner_{uuid4().hex[:6]}@example.com",
        username=f"dash_owner_{uuid4().hex[:6]}",
        hashed_password="hashed_password"
    )
    db_session.add(user)
    await db_session.commit()

    org_service = OrganizationService()
    org = await org_service.create_organization(
        db_session, user.id, OrgCreate(name="Dash Test Org", slug=f"dash-org-{uuid4().hex[:4]}")
    )

    ws_service = WorkspaceService(db_session)
    ws = await ws_service.create_workspace(name="Dash Workspace", org_id=org.id, user_id=user.id)

    proj_service = ProjectService(db_session)
    await proj_service.create_project(name="Dash Project 1", workspace_id=ws.id, org_id=org.id, user_id=user.id)
    await proj_service.create_project(name="Dash Project 2", workspace_id=ws.id, org_id=org.id, user_id=user.id)

    dash_service = DashboardService(db_session)
    data = await dash_service.get_dashboard(user.id, org.id, ws.id)

    assert data["organization"]["name"] == "Dash Test Org"
    assert data["workspace"]["name"] == "Dash Workspace"
    assert len(data["recent_projects"]) >= 2

@pytest.mark.asyncio
async def test_activity_feed_timeline(db_session: AsyncSession):
    user = User(
        email=f"act_user_{uuid4().hex[:6]}@example.com",
        username=f"act_user_{uuid4().hex[:6]}",
        hashed_password="hashed_password"
    )
    db_session.add(user)
    await db_session.commit()

    org_service = OrganizationService()
    org = await org_service.create_organization(
        db_session, user.id, OrgCreate(name="Activity Org", slug=f"act-org-{uuid4().hex[:4]}")
    )

    act_service = ActivityService(db_session)
    await act_service.record_event(
        org_id=org.id,
        user_id=user.id,
        event_type="project.created",
        metadata={"project_name": "Alpha Engine"}
    )

    timeline = await act_service.list_timeline(org_id=org.id)
    assert len(timeline) >= 1
    assert timeline[0].event_type == "project.created"


@pytest.mark.asyncio
async def test_universal_search_endpoint(db_session: AsyncSession):
    user = User(
        email=f"search_user_{uuid4().hex[:6]}@example.com",
        username=f"search_user_{uuid4().hex[:6]}",
        hashed_password="hashed_password"
    )
    db_session.add(user)
    await db_session.commit()

    org_service = OrganizationService()
    org = await org_service.create_organization(
        db_session, user.id, OrgCreate(name="Search Engine Org", slug=f"sch-org-{uuid4().hex[:4]}")
    )

    search_service = SearchService(db_session)
    res = await search_service.universal_search(
        user=user,
        query="",
        organization_id=org.id
    )
    assert res is not None
