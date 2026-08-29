from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, and_, or_, String
from sqlalchemy.orm import selectinload
from uuid import UUID
from typing import List, Optional
from datetime import datetime, timedelta
from fastapi import HTTPException, status

from ..models.user import User
from ..models.organization import Organization
from ..models.organization_member import OrganizationMember
from ..workspace.models import Workspace, WorkspaceMember
from ..projects.models import Project, ProjectMember
from ..models.invitation import Invitation
from ..models.join_request import JoinRequest
from ..models.permission import PermissionRole, PermissionMatrix
from .schemas import InvitationCreate, MemberActionPayload, JoinRequestCreate

class MemberService:
    async def list_directory(
        self, db: AsyncSession, org_id: UUID,
        workspace_id: Optional[UUID] = None, project_id: Optional[UUID] = None,
        search: Optional[str] = None, role_filter: Optional[str] = None
    ) -> List[dict]:
        # Query Organization members
        stmt = (
            select(OrganizationMember, User)
            .join(User, OrganizationMember.user_id == User.id)
            .where(
                OrganizationMember.organization_id == org_id,
                OrganizationMember.deleted_at.is_(None)
            )
        )
        if search and search.strip():
            term = f"%{search.strip()}%"
            stmt = stmt.where(or_(User.username.ilike(term), User.email.ilike(term)))

        res = await db.execute(stmt)
        org_members = res.all()

        results = []
        for org_mem, user in org_members:
            # Query workspace role if workspace_id provided
            ws_role = None
            if workspace_id:
                ws_stmt = select(WorkspaceMember.role).where(
                    WorkspaceMember.workspace_id == workspace_id,
                    WorkspaceMember.user_id == user.id,
                    WorkspaceMember.is_active == True
                )
                ws_res = await db.execute(ws_stmt)
                ws_role = ws_res.scalar_one_or_none()

            # Query project role if project_id provided
            proj_role = None
            if project_id:
                proj_stmt = select(ProjectMember.role).where(
                    ProjectMember.project_id == project_id,
                    ProjectMember.user_id == user.id,
                    ProjectMember.is_active == True
                )
                proj_res = await db.execute(proj_stmt)
                proj_role = proj_res.scalar_one_or_none()

            if role_filter and role_filter.lower() not in [
                (org_mem.role or '').lower(), (ws_role or '').lower(), (proj_role or '').lower()
            ]:
                continue

            results.append({
                "user_id": user.id,
                "username": user.username,
                "email": user.email,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "display_name": user.display_name,
                "full_name": user.full_name,
                "avatar_url": user.avatar_url,
                "status": org_mem.status or "active",
                "last_login_at": user.last_login_at,
                "joined_at": org_mem.joined_at,
                "org_role": org_mem.role or "member",
                "workspace_role": ws_role,
                "project_role": proj_role
            })

        return results

    async def update_member_action(
        self, db: AsyncSession, current_user: User, target_user_id: UUID, org_id: UUID, payload: MemberActionPayload
    ) -> dict:
        level = payload.level.lower()

        if payload.action == "transfer_ownership":
            if level == "organization":
                org = await db.get(Organization, org_id)
                if not org or org.owner_id != current_user.id:
                    raise HTTPException(status_code=403, detail="Only the organization owner can transfer ownership")
                org.owner_id = target_user_id
                # Update roles
                await db.execute(
                    update(OrganizationMember)
                    .where(OrganizationMember.organization_id == org_id, OrganizationMember.user_id == target_user_id)
                    .values(role="owner", updated_at=datetime.utcnow())
                )
                await db.execute(
                    update(OrganizationMember)
                    .where(OrganizationMember.organization_id == org_id, OrganizationMember.user_id == current_user.id)
                    .values(role="admin", updated_at=datetime.utcnow())
                )
                await db.commit()
                return {"status": "ok", "message": "Organization ownership transferred successfully"}

            elif level == "workspace" and payload.workspace_id:
                ws = await db.get(Workspace, payload.workspace_id)
                if not ws or ws.owner_id != current_user.id:
                    raise HTTPException(status_code=403, detail="Only the workspace owner can transfer ownership")
                ws.owner_id = target_user_id
                await db.execute(
                    update(WorkspaceMember)
                    .where(WorkspaceMember.workspace_id == payload.workspace_id, WorkspaceMember.user_id == target_user_id)
                    .values(role="owner", updated_at=datetime.utcnow())
                )
                await db.commit()
                return {"status": "ok", "message": "Workspace ownership transferred successfully"}

        # Standard Role/Status Updates
        if level == "organization":
            stmt = select(OrganizationMember).where(OrganizationMember.organization_id == org_id, OrganizationMember.user_id == target_user_id)
            res = await db.execute(stmt)
            mem = res.scalar_one_or_none()
            if not mem:
                raise HTTPException(status_code=404, detail="Member not found")
            if payload.role:
                mem.role = payload.role.lower()
            if payload.status:
                mem.status = payload.status
            mem.updated_at = datetime.utcnow()
            await db.commit()
            return {"status": "ok", "message": "Organization member updated"}

        elif level == "workspace" and payload.workspace_id:
            stmt = select(WorkspaceMember).where(WorkspaceMember.workspace_id == payload.workspace_id, WorkspaceMember.user_id == target_user_id)
            res = await db.execute(stmt)
            mem = res.scalar_one_or_none()
            if not mem:
                raise HTTPException(status_code=404, detail="Workspace member not found")
            if payload.role:
                mem.role = payload.role.lower()
            if payload.status:
                mem.status = payload.status
            mem.updated_at = datetime.utcnow()
            await db.commit()
            return {"status": "ok", "message": "Workspace member updated"}

        elif level == "project" and payload.project_id:
            stmt = select(ProjectMember).where(ProjectMember.project_id == payload.project_id, ProjectMember.user_id == target_user_id)
            res = await db.execute(stmt)
            mem = res.scalar_one_or_none()
            if not mem:
                raise HTTPException(status_code=404, detail="Project member not found")
            if payload.role:
                mem.role = payload.role.lower()
            if payload.status:
                mem.status = payload.status
            mem.updated_at = datetime.utcnow()
            await db.commit()
            return {"status": "ok", "message": "Project member updated"}

        raise HTTPException(status_code=400, detail="Invalid level or missing resource ID")

    async def remove_member(
        self, db: AsyncSession, current_user: User, target_user_id: UUID, org_id: UUID, level: str,
        workspace_id: Optional[UUID] = None, project_id: Optional[UUID] = None
    ):
        if level == "organization":
            org = await db.get(Organization, org_id)
            if org and org.owner_id == target_user_id:
                raise HTTPException(status_code=400, detail="Cannot remove the organization owner. Transfer ownership first.")
            await db.execute(
                delete(OrganizationMember).where(OrganizationMember.organization_id == org_id, OrganizationMember.user_id == target_user_id)
            )
            await db.commit()

        elif level == "workspace" and workspace_id:
            await db.execute(
                delete(WorkspaceMember).where(WorkspaceMember.workspace_id == workspace_id, WorkspaceMember.user_id == target_user_id)
            )
            await db.commit()

        elif level == "project" and project_id:
            await db.execute(
                delete(ProjectMember).where(ProjectMember.project_id == project_id, ProjectMember.user_id == target_user_id)
            )
            await db.commit()


class EnterpriseInvitationService:
    async def issue_invitation(self, db: AsyncSession, current_user: User, invitation_in: InvitationCreate) -> Invitation:
        clean_email = (invitation_in.email or '').strip().lower()
        if not clean_email or '@' not in clean_email:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid email address format")

        if current_user.email and current_user.email.strip().lower() == clean_email:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="You cannot send an invitation to yourself")

        # Verify user has permission to invite in the target organization
        org_mem_stmt = select(OrganizationMember).options(selectinload(OrganizationMember.role_rel)).where(
            OrganizationMember.organization_id == invitation_in.organization_id,
            OrganizationMember.user_id == current_user.id,
            OrganizationMember.deleted_at.is_(None)
        )
        mem_res = await db.execute(org_mem_stmt)
        mem = mem_res.scalar_one_or_none()

        user_role = (mem.role or '').lower() if mem else ''
        rel_role = (mem.role_rel.name if mem and getattr(mem, 'role_rel', None) and hasattr(mem.role_rel, 'name') and mem.role_rel.name else '').lower()
        allowed_roles = ["owner", "admin", "super_admin", "org_admin"]

        if not mem or (user_role not in allowed_roles and rel_role not in allowed_roles):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Permission denied. Only organization owners and admins can issue invitations.")

        # Verify target user is not already a member of the organization
        target_user_stmt = select(User.id).where(User.email == clean_email, User.deleted_at.is_(None))
        target_user_id = (await db.execute(target_user_stmt)).scalar_one_or_none()
        if target_user_id:
            org_mem_check = select(OrganizationMember.id).where(
                OrganizationMember.organization_id == invitation_in.organization_id,
                OrganizationMember.user_id == target_user_id,
                OrganizationMember.deleted_at.is_(None)
            )
            if (await db.execute(org_mem_check)).scalar_one_or_none():
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User is already a member of this organization")

        # Check existing pending invitation
        stmt = select(Invitation).where(
            Invitation.organization_id == invitation_in.organization_id,
            Invitation.email == clean_email,
            Invitation.status == "pending",
            Invitation.deleted_at.is_(None)
        )
        res = await db.execute(stmt)
        existing = res.scalar_one_or_none()
        if existing:
            if existing.expires_at > datetime.utcnow():
                return existing
            existing.status = "expired"

        invitation = Invitation(
            organization_id=invitation_in.organization_id,
            workspace_id=invitation_in.workspace_id,
            project_id=invitation_in.project_id,
            email=clean_email,
            mobile=invitation_in.mobile,
            role=invitation_in.role.lower(),
            token=Invitation.generate_token(),
            invited_by=current_user.id,
            status="pending",
            expires_at=datetime.utcnow() + timedelta(days=7),
            created_by=str(current_user.id)
        )
        db.add(invitation)
        await db.commit()
        await db.refresh(invitation)

        if target_user_id:
            try:
                from ..notifications.service import NotificationService
                notif_service = NotificationService(db)
                org = await db.get(Organization, invitation_in.organization_id)
                org_name = org.name if org else "Organization"
                inviter_name = current_user.username if current_user and current_user.username else "An admin"

                await notif_service.create_notification(
                    user_id=target_user_id,
                    organization_id=invitation_in.organization_id,
                    title=f"Organization Invitation",
                    message=f"{inviter_name} invited you to join {org_name} as {invitation_in.role}.",
                    type="invitation",
                    priority="high",
                    link="/invitations",
                    entity_type="invitation",
                    entity_id=invitation.id
                )
                await db.commit()
            except Exception as e:
                pass

        return invitation

    async def list_user_invitations(self, db: AsyncSession, email: str) -> List[Invitation]:
        stmt = (
            select(Invitation)
            .options(selectinload(Invitation.organization), selectinload(Invitation.workspace), selectinload(Invitation.project))
            .where(
                Invitation.email == email,
                Invitation.status == "pending",
                Invitation.deleted_at.is_(None)
            )
        )
        res = await db.execute(stmt)
        return list(res.scalars().all())

    async def accept_invitation(self, db: AsyncSession, token_or_id: str, user: User) -> dict:
        stmt = (
            select(Invitation)
            .where(
                (Invitation.token == token_or_id) | (Invitation.id.cast(String) == token_or_id),
                Invitation.deleted_at.is_(None)
            )
        )
        res = await db.execute(stmt)
        inv = res.scalar_one_or_none()
        if not inv or inv.status != "pending":
            raise HTTPException(status_code=400, detail="Invalid or expired invitation")

        if inv.expires_at < datetime.utcnow():
            inv.status = "expired"
            await db.commit()
            raise HTTPException(status_code=400, detail="Invitation has expired")

        # 1. Provision Organization Member
        org_mem_stmt = select(OrganizationMember).where(
            OrganizationMember.organization_id == inv.organization_id,
            OrganizationMember.user_id == user.id
        )
        org_mem_res = await db.execute(org_mem_stmt)
        existing_org_mem = org_mem_res.scalar_one_or_none()
        if not existing_org_mem:
            org_mem = OrganizationMember(
                organization_id=inv.organization_id,
                user_id=user.id,
                role=inv.role,
                status="active",
                joined_at=datetime.utcnow()
            )
            db.add(org_mem)

        # 2. Provision Workspace Member if specified or default workspace
        target_ws_id = inv.workspace_id
        if not target_ws_id:
            def_ws_stmt = select(Workspace.id).where(Workspace.organization_id == inv.organization_id, Workspace.is_default == True)
            def_ws_res = await db.execute(def_ws_stmt)
            target_ws_id = def_ws_res.scalar_one_or_none()

        if target_ws_id:
            ws_mem_stmt = select(WorkspaceMember).where(
                WorkspaceMember.workspace_id == target_ws_id,
                WorkspaceMember.user_id == user.id
            )
            ws_mem_res = await db.execute(ws_mem_stmt)
            existing_ws_mem = ws_mem_res.scalar_one_or_none()
            if not existing_ws_mem:
                ws_mem = WorkspaceMember(
                    workspace_id=target_ws_id,
                    user_id=user.id,
                    role=inv.role,
                    status="active"
                )
                db.add(ws_mem)

        # 3. Provision Project Member if specified
        if inv.project_id:
            proj_mem_stmt = select(ProjectMember).where(
                ProjectMember.project_id == inv.project_id,
                ProjectMember.user_id == user.id
            )
            proj_mem_res = await db.execute(proj_mem_stmt)
            existing_proj_mem = proj_mem_res.scalar_one_or_none()
            if not existing_proj_mem:
                proj_mem = ProjectMember(
                    project_id=inv.project_id,
                    user_id=user.id,
                    role=inv.role,
                    status="active"
                )
                db.add(proj_mem)

        # Set user's active context
        user.current_organization_id = inv.organization_id
        if target_ws_id:
            user.current_workspace_id = target_ws_id

        inv.status = "accepted"
        inv.updated_at = datetime.utcnow()
        await db.commit()
        return {"status": "ok", "message": "Invitation accepted successfully"}

    async def reject_invitation(self, db: AsyncSession, invite_id: UUID, user: User) -> dict:
        inv = await db.get(Invitation, invite_id)
        if not inv or inv.email != user.email:
            raise HTTPException(status_code=404, detail="Invitation not found")
        inv.status = "rejected"
        inv.updated_at = datetime.utcnow()
        await db.commit()
        return {"status": "ok", "message": "Invitation rejected"}

    async def cancel_invitation(self, db: AsyncSession, invite_id: UUID, org_id: UUID) -> dict:
        inv = await db.get(Invitation, invite_id)
        if not inv or inv.organization_id != org_id:
            raise HTTPException(status_code=404, detail="Invitation not found")
        inv.status = "cancelled"
        inv.updated_at = datetime.utcnow()
        await db.commit()
        return {"status": "ok", "message": "Invitation cancelled"}


class JoinRequestService:
    async def request_access(self, db: AsyncSession, user: User, req_in: JoinRequestCreate) -> JoinRequest:
        stmt = select(JoinRequest).where(
            JoinRequest.organization_id == req_in.organization_id,
            JoinRequest.user_id == user.id,
            JoinRequest.status == "pending"
        )
        res = await db.execute(stmt)
        existing = res.scalar_one_or_none()
        if existing:
            return existing

        req = JoinRequest(
            organization_id=req_in.organization_id,
            workspace_id=req_in.workspace_id,
            project_id=req_in.project_id,
            user_id=user.id,
            message=req_in.message,
            status="pending",
            created_by=str(user.id)
        )
        db.add(req)
        await db.commit()
        await db.refresh(req)
        return req

    async def list_join_requests(self, db: AsyncSession, org_id: UUID) -> List[JoinRequest]:
        stmt = (
            select(JoinRequest)
            .options(selectinload(JoinRequest.user), selectinload(JoinRequest.organization))
            .where(
                JoinRequest.organization_id == org_id,
                JoinRequest.status == "pending",
                JoinRequest.deleted_at.is_(None)
            )
        )
        res = await db.execute(stmt)
        return list(res.scalars().all())

    async def approve_request(self, db: AsyncSession, request_id: UUID, org_id: UUID) -> dict:
        req = await db.get(JoinRequest, request_id)
        if not req or req.organization_id != org_id or req.status != "pending":
            raise HTTPException(status_code=404, detail="Join request not found or resolved")

        # Provision Member
        org_mem_stmt = select(OrganizationMember).where(
            OrganizationMember.organization_id == req.organization_id,
            OrganizationMember.user_id == req.user_id
        )
        org_mem_res = await db.execute(org_mem_stmt)
        if not org_mem_res.scalar_one_or_none():
            db.add(OrganizationMember(
                organization_id=req.organization_id,
                user_id=req.user_id,
                role="member",
                status="active"
            ))

        req.status = "approved"
        req.updated_at = datetime.utcnow()
        await db.commit()
        return {"status": "ok", "message": "Join request approved"}

    async def reject_request(self, db: AsyncSession, request_id: UUID, org_id: UUID) -> dict:
        req = await db.get(JoinRequest, request_id)
        if not req or req.organization_id != org_id:
            raise HTTPException(status_code=404, detail="Join request not found")

        req.status = "rejected"
        req.updated_at = datetime.utcnow()
        await db.commit()
        return {"status": "ok", "message": "Join request rejected"}
