import pytest
import pytest_asyncio
from uuid import uuid4
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.models.organization import Organization
from app.organizations.service import OrganizationService
from app.organizations.schemas import OrgCreate, OrgUpdate, MemberInvite, OrgSettingsUpdate
from app.workspace.service import WorkspaceService
from app.workspace.schemas import WorkspaceCreate, WorkspaceUpdate

@pytest.mark.asyncio
async def test_personal_org_and_default_workspace_creation(db_session: AsyncSession):
    user = User(
        email=f"tenant_user_{uuid4().hex[:6]}@example.com",
        username=f"tenant_user_{uuid4().hex[:6]}",
        hashed_password="hashed_password",
        first_name="MultiTenant",
        last_name="Tester"
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    org_service = OrganizationService()
    org = await org_service.ensure_user_personal_org(db_session, user)

    assert org is not None
    assert org.is_personal is True
    assert org.owner_id == user.id

    settings = await org_service.get_settings(db_session, org.id)
    assert settings is not None
    assert settings.timezone == "UTC"

    ws_service = WorkspaceService(db_session)
    workspaces = await ws_service.list_workspaces(org.id)
    assert len(workspaces) >= 1
    assert any(w.is_default for w in workspaces)

@pytest.mark.asyncio
async def test_organization_crud_and_settings(db_session: AsyncSession):
    user = User(
        email=f"org_owner_{uuid4().hex[:6]}@example.com",
        username=f"org_owner_{uuid4().hex[:6]}",
        hashed_password="hashed_password"
    )
    db_session.add(user)
    await db_session.commit()

    org_service = OrganizationService()
    slug = f"acme-corp-{uuid4().hex[:4]}"
    org_in = OrgCreate(
        name="Acme Corporation",
        slug=slug,
        description="Global innovation company",
        website="https://acme.example.com",
        industry="Technology"
    )
    org = await org_service.create_organization(db_session, user.id, org_in)

    assert org.name == "Acme Corporation"
    assert org.slug == slug
    assert org.website == "https://acme.example.com"

    # Update Org
    updated_org = await org_service.update_organization(
        db_session, org.id, OrgUpdate(description="Updated Innovation Corp", branding_color="#10B981")
    )
    assert updated_org.description == "Updated Innovation Corp"

    # Update Settings
    settings = await org_service.update_settings(
        db_session, org.id, OrgSettingsUpdate(theme="dark", branding_color="#10B981", allow_public_invites=True)
    )
    assert settings.branding_color == "#10B981"
    assert settings.allow_public_invites is True

@pytest.mark.asyncio
async def test_workspace_crud_and_archiving(db_session: AsyncSession):
    user = User(
        email=f"ws_user_{uuid4().hex[:6]}@example.com",
        username=f"ws_user_{uuid4().hex[:6]}",
        hashed_password="hashed_password"
    )
    db_session.add(user)
    await db_session.commit()

    org_service = OrganizationService()
    slug = f"tech-org-{uuid4().hex[:4]}"
    org = await org_service.create_organization(db_session, user.id, OrgCreate(name="Tech Org", slug=slug))

    ws_service = WorkspaceService(db_session)
    ws = await ws_service.create_workspace(
        name="Engineering",
        org_id=org.id,
        user_id=user.id,
        description="Engineering and architecture discussions",
        color="#8B5CF6"
    )

    assert ws.name == "Engineering"
    assert ws.organization_id == org.id

    # Archive
    archived = await ws_service.archive_workspace(ws.id, org.id)
    assert archived.is_archived is True

    # Restore
    restored = await ws_service.restore_workspace(ws.id, org.id)
    assert restored.is_archived is False

@pytest.mark.asyncio
async def test_organization_invitation_flow(db_session: AsyncSession):
    inviter = User(
        email=f"inviter_{uuid4().hex[:6]}@example.com",
        username=f"inviter_{uuid4().hex[:6]}",
        hashed_password="hashed_password"
    )
    invitee = User(
        email=f"invitee_{uuid4().hex[:6]}@example.com",
        username=f"invitee_{uuid4().hex[:6]}",
        hashed_password="hashed_password"
    )
    db_session.add_all([inviter, invitee])
    await db_session.commit()

    org_service = OrganizationService()
    slug = f"invite-org-{uuid4().hex[:4]}"
    org = await org_service.create_organization(db_session, inviter.id, OrgCreate(name="Invite Org", slug=slug))

    invite = await org_service.invite_member(
        db_session, org.id, MemberInvite(email=invitee.email, role="manager"), inviter.id
    )

    assert invite.email == invitee.email
    assert invite.status == "pending"

    # Accept Invite
    result = await org_service.accept_invitation(db_session, invite.token, invitee)
    assert result["status"] == "ok"

    members = await org_service.list_members(db_session, org.id)
    emails = [m["email"] for m in members]
    assert invitee.email in emails
