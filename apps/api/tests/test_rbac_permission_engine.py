import pytest
from uuid import uuid4
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException

from app.models.user import User
from app.organizations.service import OrganizationService
from app.organizations.schemas import OrgCreate
from app.workspace.service import WorkspaceService
from app.projects.service import ProjectService
from app.members.service import MemberService, EnterpriseInvitationService
from app.members.schemas import InvitationCreate, MemberActionPayload
from app.permissions.service import PermissionService

@pytest.mark.asyncio
async def test_system_role_permissions(db_session: AsyncSession):
    owner = User(
        email=f"rbac_owner_{uuid4().hex[:6]}@example.com",
        username=f"rbac_owner_{uuid4().hex[:6]}",
        hashed_password="hashed_password"
    )
    viewer = User(
        email=f"rbac_viewer_{uuid4().hex[:6]}@example.com",
        username=f"rbac_viewer_{uuid4().hex[:6]}",
        hashed_password="hashed_password"
    )
    db_session.add_all([owner, viewer])
    await db_session.commit()

    org_service = OrganizationService()
    org = await org_service.create_organization(
        db_session, owner.id, OrgCreate(name="RBAC Org", slug=f"rbac-org-{uuid4().hex[:4]}")
    )

    invite_service = EnterpriseInvitationService()
    inv = await invite_service.issue_invitation(
        db_session, owner, InvitationCreate(organization_id=org.id, email=viewer.email, role="viewer")
    )
    await invite_service.accept_invitation(db_session, inv.token, viewer)

    perm_service = PermissionService()

    # Owner checks
    assert await perm_service.has_permission(db_session, owner.id, org.id, "organization.delete") is True
    assert await perm_service.has_permission(db_session, owner.id, org.id, "project.edit") is True

    # Viewer checks
    assert await perm_service.has_permission(db_session, viewer.id, org.id, "project.view") is True
    assert await perm_service.has_permission(db_session, viewer.id, org.id, "project.delete") is False
    assert await perm_service.has_permission(db_session, viewer.id, org.id, "organization.edit") is False

@pytest.mark.asyncio
async def test_permission_checker_dependency(db_session: AsyncSession):
    admin = User(
        email=f"rbac_admin_{uuid4().hex[:6]}@example.com",
        username=f"rbac_admin_{uuid4().hex[:6]}",
        hashed_password="hashed_password"
    )
    guest = User(
        email=f"rbac_guest_{uuid4().hex[:6]}@example.com",
        username=f"rbac_guest_{uuid4().hex[:6]}",
        hashed_password="hashed_password"
    )
    db_session.add_all([admin, guest])
    await db_session.commit()

    org_service = OrganizationService()
    org = await org_service.create_organization(
        db_session, admin.id, OrgCreate(name="RBAC Guard Org", slug=f"rbac-gd-{uuid4().hex[:4]}")
    )

    invite_service = EnterpriseInvitationService()
    inv = await invite_service.issue_invitation(
        db_session, admin, InvitationCreate(organization_id=org.id, email=guest.email, role="guest")
    )
    await invite_service.accept_invitation(db_session, inv.token, guest)

    perm_service = PermissionService()

    # Require permission allowed
    await perm_service.require_permission(db_session, admin.id, org.id, "project.create")

    # Require permission denied -> 403 HTTP Exception
    with pytest.raises(HTTPException) as exc_info:
        await perm_service.require_permission(db_session, guest.id, org.id, "project.create")
    assert exc_info.value.status_code == 403

@pytest.mark.asyncio
async def test_cross_tenant_rbac_isolation(db_session: AsyncSession):
    user_a = User(
        email=f"user_a_{uuid4().hex[:6]}@example.com",
        username=f"user_a_{uuid4().hex[:6]}",
        hashed_password="hashed_password"
    )
    user_b = User(
        email=f"user_b_{uuid4().hex[:6]}@example.com",
        username=f"user_b_{uuid4().hex[:6]}",
        hashed_password="hashed_password"
    )
    db_session.add_all([user_a, user_b])
    await db_session.commit()

    org_service = OrganizationService()
    org_a = await org_service.create_organization(
        db_session, user_a.id, OrgCreate(name="Org A", slug=f"org-a-{uuid4().hex[:4]}")
    )
    org_b = await org_service.create_organization(
        db_session, user_b.id, OrgCreate(name="Org B", slug=f"org-b-{uuid4().hex[:4]}")
    )

    perm_service = PermissionService()

    # User A has no permissions in Org B
    assert await perm_service.has_permission(db_session, user_a.id, org_b.id, "project.view") is False

    # User B has no permissions in Org A
    assert await perm_service.has_permission(db_session, user_b.id, org_a.id, "project.view") is False
