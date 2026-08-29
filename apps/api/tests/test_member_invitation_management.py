import pytest
from uuid import uuid4
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.organizations.service import OrganizationService
from app.organizations.schemas import OrgCreate
from app.workspace.service import WorkspaceService
from app.projects.service import ProjectService
from app.members.service import MemberService, EnterpriseInvitationService, JoinRequestService
from app.members.schemas import InvitationCreate, MemberActionPayload, JoinRequestCreate

@pytest.mark.asyncio
async def test_issue_and_accept_multi_level_invitation(db_session: AsyncSession):
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
    org = await org_service.create_organization(
        db_session, inviter.id, OrgCreate(name="MultiLevel Org", slug=f"mult-org-{uuid4().hex[:4]}")
    )

    ws_service = WorkspaceService(db_session)
    ws = await ws_service.create_workspace(name="Dev Workspace", org_id=org.id, user_id=inviter.id)

    proj_service = ProjectService(db_session)
    proj = await proj_service.create_project(name="Core API Project", workspace_id=ws.id, org_id=org.id, user_id=inviter.id)

    invite_service = EnterpriseInvitationService()
    inv_in = InvitationCreate(
        organization_id=org.id,
        workspace_id=ws.id,
        project_id=proj.id,
        email=invitee.email,
        role="manager"
    )
    inv = await invite_service.issue_invitation(db_session, inviter, inv_in)

    assert inv.email == invitee.email
    assert inv.role == "manager"
    assert inv.status == "pending"

    # Accept invitation
    res = await invite_service.accept_invitation(db_session, inv.token, invitee)
    assert res["status"] == "ok"

    # Check directory
    member_service = MemberService()
    directory = await member_service.list_directory(db_session, org.id, workspace_id=ws.id, project_id=proj.id)
    emails = [m["email"] for m in directory]
    assert invitee.email in emails

@pytest.mark.asyncio
async def test_reject_and_cancel_invitation(db_session: AsyncSession):
    manager = User(
        email=f"manager_{uuid4().hex[:6]}@example.com",
        username=f"manager_{uuid4().hex[:6]}",
        hashed_password="hashed_password"
    )
    invitee1 = User(
        email=f"rej_user_{uuid4().hex[:6]}@example.com",
        username=f"rej_user_{uuid4().hex[:6]}",
        hashed_password="hashed_password"
    )
    db_session.add_all([manager, invitee1])
    await db_session.commit()

    org_service = OrganizationService()
    org = await org_service.create_organization(
        db_session, manager.id, OrgCreate(name="Cancel Org", slug=f"can-org-{uuid4().hex[:4]}")
    )

    invite_service = EnterpriseInvitationService()
    inv1 = await invite_service.issue_invitation(
        db_session, manager, InvitationCreate(organization_id=org.id, email=invitee1.email, role="member")
    )
    inv2 = await invite_service.issue_invitation(
        db_session, manager, InvitationCreate(organization_id=org.id, email="other@example.com", role="member")
    )

    # Reject
    rej_res = await invite_service.reject_invitation(db_session, inv1.id, invitee1)
    assert rej_res["status"] == "ok"

    # Cancel
    can_res = await invite_service.cancel_invitation(db_session, inv2.id, org.id)
    assert can_res["status"] == "ok"

@pytest.mark.asyncio
async def test_member_directory_and_role_actions(db_session: AsyncSession):
    owner = User(
        email=f"roster_owner_{uuid4().hex[:6]}@example.com",
        username=f"roster_owner_{uuid4().hex[:6]}",
        hashed_password="hashed_password"
    )
    member = User(
        email=f"roster_mem_{uuid4().hex[:6]}@example.com",
        username=f"roster_mem_{uuid4().hex[:6]}",
        hashed_password="hashed_password"
    )
    db_session.add_all([owner, member])
    await db_session.commit()

    org_service = OrganizationService()
    org = await org_service.create_organization(
        db_session, owner.id, OrgCreate(name="Roster Org", slug=f"ros-org-{uuid4().hex[:4]}")
    )

    invite_service = EnterpriseInvitationService()
    inv = await invite_service.issue_invitation(
        db_session, owner, InvitationCreate(organization_id=org.id, email=member.email, role="contributor")
    )
    await invite_service.accept_invitation(db_session, inv.token, member)

    member_service = MemberService()
    # Promote to Admin
    await member_service.update_member_action(
        db_session, owner, member.id, org.id, MemberActionPayload(level="organization", role="admin")
    )

    directory = await member_service.list_directory(db_session, org.id)
    target_mem = next(m for m in directory if m["user_id"] == member.id)
    assert target_mem["org_role"] == "admin"

    # Suspend Member
    await member_service.update_member_action(
        db_session, owner, member.id, org.id, MemberActionPayload(level="organization", status="suspended")
    )
    directory_after = await member_service.list_directory(db_session, org.id)
    suspended_mem = next(m for m in directory_after if m["user_id"] == member.id)
    assert suspended_mem["status"] == "suspended"

@pytest.mark.asyncio
async def test_transfer_ownership(db_session: AsyncSession):
    old_owner = User(
        email=f"old_owner_{uuid4().hex[:6]}@example.com",
        username=f"old_owner_{uuid4().hex[:6]}",
        hashed_password="hashed_password"
    )
    new_owner = User(
        email=f"new_owner_{uuid4().hex[:6]}@example.com",
        username=f"new_owner_{uuid4().hex[:6]}",
        hashed_password="hashed_password"
    )
    db_session.add_all([old_owner, new_owner])
    await db_session.commit()

    org_service = OrganizationService()
    org = await org_service.create_organization(
        db_session, old_owner.id, OrgCreate(name="Transfer Org", slug=f"trans-org-{uuid4().hex[:4]}")
    )

    # Invite new owner
    invite_service = EnterpriseInvitationService()
    inv = await invite_service.issue_invitation(
        db_session, old_owner, InvitationCreate(organization_id=org.id, email=new_owner.email, role="admin")
    )
    await invite_service.accept_invitation(db_session, inv.token, new_owner)

    member_service = MemberService()
    # Transfer Ownership
    res = await member_service.update_member_action(
        db_session, old_owner, new_owner.id, org.id, MemberActionPayload(action="transfer_ownership", level="organization")
    )
    assert res["status"] == "ok"

    updated_org = await org_service.get_organization(db_session, org.id)
    assert updated_org.owner_id == new_owner.id

@pytest.mark.asyncio
async def test_join_requests_workflow(db_session: AsyncSession):
    owner = User(
        email=f"jr_owner_{uuid4().hex[:6]}@example.com",
        username=f"jr_owner_{uuid4().hex[:6]}",
        hashed_password="hashed_password"
    )
    requester = User(
        email=f"requester_{uuid4().hex[:6]}@example.com",
        username=f"requester_{uuid4().hex[:6]}",
        hashed_password="hashed_password"
    )
    db_session.add_all([owner, requester])
    await db_session.commit()

    org_service = OrganizationService()
    org = await org_service.create_organization(
        db_session, owner.id, OrgCreate(name="Join Org", slug=f"join-org-{uuid4().hex[:4]}")
    )

    join_service = JoinRequestService()
    req = await join_service.request_access(
        db_session, requester, JoinRequestCreate(organization_id=org.id, message="Please let me join!")
    )
    assert req.status == "pending"

    # List pending requests
    pending_list = await join_service.list_join_requests(db_session, org.id)
    assert len(pending_list) >= 1

    # Approve request
    app_res = await join_service.approve_request(db_session, req.id, org.id)
    assert app_res["status"] == "ok"

    member_service = MemberService()
    directory = await member_service.list_directory(db_session, org.id)
    emails = [m["email"] for m in directory]
    assert requester.email in emails
