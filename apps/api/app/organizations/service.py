import secrets
import logging
from datetime import datetime, timedelta
from uuid import UUID
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, String
from fastapi import HTTPException, status

logger = logging.getLogger(__name__)

from .repository import OrganizationRepository
from .schemas import OrgCreate, OrgUpdate, MemberInvite, OrgSettingsUpdate
from ..models.organization import Organization, OrganizationSettings, OrganizationInvitation
from ..models.organization_member import OrganizationMember
from ..models.user import User
from ..workspace.service import WorkspaceService
from ..workspace.models import Workspace, WorkspaceMember, WorkspaceSettings

class OrganizationService:
    def __init__(self):
        self.repo = OrganizationRepository()

    async def create_organization(self, db: AsyncSession, user_id: UUID, org_in: OrgCreate, is_personal: bool = False) -> Organization:
        existing = await self.repo.get_organization_by_slug(db, org_in.slug)
        if existing:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Organization slug already exists")

        new_org = Organization(
            name=org_in.name,
            slug=org_in.slug,
            description=org_in.description,
            logo_url=org_in.logo_url,
            website=org_in.website,
            industry=org_in.industry,
            country=org_in.country,
            timezone=org_in.timezone or "UTC",
            language=org_in.language or "en",
            owner_id=user_id,
            is_personal=is_personal,
            created_by=str(user_id) if user_id else None
        )
        await self.repo.create_organization(db, new_org)
        await db.flush()

        # Create Default Organization Settings
        org_settings = OrganizationSettings(
            organization_id=new_org.id,
            default_language=new_org.language,
            timezone=new_org.timezone,
            theme="dark",
            branding_color="#3B82F6",
            allow_public_invites=False,
            allow_guest_access=True
        )
        await self.repo.save_settings(db, org_settings)

        # Add owner member
        member = OrganizationMember(
            organization_id=new_org.id,
            user_id=user_id,
            role="owner",
            status="active"
        )
        await self.repo.add_member(db, member)

        # Create Default Workspace ("General")
        ws_service = WorkspaceService(db)
        default_ws = await ws_service.create_workspace(
            name="General",
            org_id=new_org.id,
            user_id=user_id,
            description="Default workspace for general discussions and files",
            color="#3B82F6"
        )
        default_ws.is_default = True
        default_ws.owner_id = user_id

        # Create Default Workspace Settings
        ws_settings = WorkspaceSettings(
            workspace_id=default_ws.id,
            theme="dark",
            timezone=new_org.timezone,
            language=new_org.language,
            default_dashboard="overview",
            allow_ai=True
        )
        db.add(ws_settings)

        await db.commit()
        return await self.get_organization(db, new_org.id)

    async def ensure_user_personal_org(self, db: AsyncSession, user: User) -> Organization:
        user_orgs = await self.repo.list_user_organizations(db, user.id)
        if user_orgs:
            # Return first org or user's active org
            for m in user_orgs:
                if m.organization and m.organization.id == user.current_organization_id:
                    return m.organization
            return user_orgs[0].organization

        # Auto-provision Personal Organization
        base_name = f"{user.first_name}'s Org" if user.first_name else f"{user.username}'s Personal Org"
        slug_base = (user.username or user.email.split('@')[0]).lower()
        import re
        slug_base = re.sub(r'[^a-z0-9]', '-', slug_base)
        slug = slug_base
        counter = 1
        while await self.repo.get_organization_by_slug(db, slug):
            slug = f"{slug_base}-{counter}"
            counter += 1

        org_in = OrgCreate(
            name=base_name,
            slug=slug,
            description="Personal workspace organization",
            timezone=user.timezone or "UTC",
            language=user.language or "en"
        )
        org = await self.create_organization(db, user.id, org_in, is_personal=True)
        user.current_organization_id = org.id

        # Find created default workspace
        ws_stmt = select(Workspace).where(Workspace.organization_id == org.id, Workspace.is_default == True)
        ws_res = await db.execute(ws_stmt)
        def_ws = ws_res.scalar_one_or_none()
        if def_ws:
            user.current_workspace_id = def_ws.id

        db.add(user)
        await db.commit()
        return org

    async def get_organization(self, db: AsyncSession, org_id: UUID) -> Organization:
        org = await self.repo.get_organization(db, org_id)
        if not org:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Organization not found")
        return org

    async def update_organization(self, db: AsyncSession, org_id: UUID, org_in: OrgUpdate) -> Organization:
        org = await self.get_organization(db, org_id)
        if org_in.name is not None:
            org.name = org_in.name
        if org_in.description is not None:
            org.description = org_in.description
        if org_in.logo_url is not None:
            org.logo_url = org_in.logo_url
        if org_in.website is not None:
            org.website = org_in.website
        if org_in.industry is not None:
            org.industry = org_in.industry
        if org_in.country is not None:
            org.country = org_in.country
        if org_in.timezone is not None:
            org.timezone = org_in.timezone
        if org_in.language is not None:
            org.language = org_in.language
        if org_in.visibility is not None:
            org.visibility = org_in.visibility
        if org_in.status is not None:
            org.status = org_in.status

        await db.commit()
        await db.refresh(org)
        return org

    async def get_settings(self, db: AsyncSession, org_id: UUID) -> OrganizationSettings:
        settings_obj = await self.repo.get_settings(db, org_id)
        if not settings_obj:
            settings_obj = OrganizationSettings(organization_id=org_id)
            await self.repo.save_settings(db, settings_obj)
            await db.commit()
        return settings_obj

    async def update_settings(self, db: AsyncSession, org_id: UUID, update_in: OrgSettingsUpdate) -> OrganizationSettings:
        settings_obj = await self.get_settings(db, org_id)
        if update_in.default_language is not None:
            settings_obj.default_language = update_in.default_language
        if update_in.timezone is not None:
            settings_obj.timezone = update_in.timezone
        if update_in.theme is not None:
            settings_obj.theme = update_in.theme
        if update_in.branding_color is not None:
            settings_obj.branding_color = update_in.branding_color
        if update_in.allow_public_invites is not None:
            settings_obj.allow_public_invites = update_in.allow_public_invites
        if update_in.allow_guest_access is not None:
            settings_obj.allow_guest_access = update_in.allow_guest_access

        await db.commit()
        await db.refresh(settings_obj)
        return settings_obj

    async def delete_organization(self, db: AsyncSession, org_id: UUID) -> None:
        org = await self.get_organization(db, org_id)
        org.deleted_at = datetime.utcnow()
        await db.commit()

    async def list_user_organizations(self, db: AsyncSession, user_id: UUID) -> List[dict]:
        memberships = await self.repo.list_user_organizations(db, user_id)
        orgs = []
        for m in memberships:
            if m.organization and not m.organization.deleted_at:
                s = m.organization.settings
                settings_dict = {
                    "default_language": s.default_language if s else "en",
                    "timezone": s.timezone if s else "UTC",
                    "theme": s.theme if s else "dark",
                    "branding_color": s.branding_color if s else "#3B82F6",
                    "allow_public_invites": s.allow_public_invites if s else False,
                    "allow_guest_access": s.allow_guest_access if s else True
                }
                orgs.append({
                    "id": m.organization.id,
                    "name": m.organization.name,
                    "slug": m.organization.slug,
                    "description": m.organization.description,
                    "logo_url": m.organization.logo_url,
                    "website": m.organization.website,
                    "industry": m.organization.industry,
                    "country": m.organization.country,
                    "timezone": m.organization.timezone,
                    "language": m.organization.language,
                    "role": m.role,
                    "status": m.organization.status,
                    "visibility": m.organization.visibility,
                    "is_personal": m.organization.is_personal,
                    "owner_id": m.organization.owner_id,
                    "created_at": m.organization.created_at,
                    "settings": settings_dict
                })
        return orgs

    async def invite_member(
        self, db: AsyncSession, org_id: UUID, invite_in: MemberInvite, inviter_id: UUID, current_user_email: Optional[str] = None
    ) -> OrganizationInvitation:
        clean_email = (invite_in.email or '').strip().lower()
        if not clean_email or '@' not in clean_email:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid email address format")

        if current_user_email and current_user_email.strip().lower() == clean_email:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="You cannot send an invitation to yourself")

        # Check existing membership if user already exists
        user_stmt = select(User).where(User.email == clean_email, User.deleted_at == None)
        user_res = await db.execute(user_stmt)
        target_user = user_res.scalar_one_or_none()

        if target_user:
            existing_mem = await self.repo.get_membership(db, org_id, target_user.id)
            if existing_mem:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User is already a member of this organization")

        # Check existing pending invitation
        existing_invite = await self.repo.get_pending_invitation(db, org_id, clean_email)
        if existing_invite:
            if existing_invite.expires_at > datetime.utcnow():
                return existing_invite
            existing_invite.status = "expired"

        token = secrets.token_urlsafe(32)
        invitation = OrganizationInvitation(
            organization_id=org_id,
            email=clean_email,
            role=invite_in.role.lower(),
            token=token,
            invited_by=inviter_id,
            status="pending",
            expires_at=datetime.utcnow() + timedelta(days=7)
        )
        await self.repo.create_invitation(db, invitation)
        await db.commit()
        await db.refresh(invitation)

        # Create in-app notification if target user exists
        if target_user:
            try:
                from ..notifications.service import NotificationService
                notif_service = NotificationService(db)
                org = await self.get_organization(db, org_id)
                org_name = org.name if org else "Organization"
                inviter_stmt = select(User).where(User.id == inviter_id)
                inviter_res = await db.execute(inviter_stmt)
                inviter = inviter_res.scalar_one_or_none()
                inviter_name = inviter.username if inviter else "An admin"

                await notif_service.create_notification(
                    user_id=target_user.id,
                    organization_id=org_id,
                    title=f"Organization Invitation",
                    message=f"{inviter_name} invited you to join {org_name} as {invite_in.role}.",
                    type="invitation",
                    priority="high",
                    link="/invitations",
                    entity_type="organization_invitation",
                    entity_id=invitation.id
                )
                await db.commit()
            except Exception as e:
                import traceback
                traceback.print_exc()
                logger.warning(f"Failed to create invitation notification for {clean_email}: {e}")

        # Non-blocking email notification log
        try:
            logger.info(f"Invitation created for {clean_email} in org {org_id} with token {token}")
        except Exception as e:
            logger.warning(f"Failed to process email log notification for {clean_email}: {e}")

        return invitation

    async def accept_invitation(self, db: AsyncSession, token_or_id: str, user: User) -> dict:
        invite = None
        try:
            invite_uuid = UUID(token_or_id)
            stmt = select(OrganizationInvitation).where(
                OrganizationInvitation.id == invite_uuid,
                OrganizationInvitation.deleted_at == None
            )
            res = await db.execute(stmt)
            invite = res.scalar_one_or_none()
        except (ValueError, TypeError):
            pass

        if not invite:
            stmt = select(OrganizationInvitation).where(
                OrganizationInvitation.token == token_or_id,
                OrganizationInvitation.deleted_at == None
            )
            res = await db.execute(stmt)
            invite = res.scalar_one_or_none()

        if not invite or invite.status != "pending":
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or expired invitation")

        if invite.expires_at < datetime.utcnow():
            invite.status = "expired"
            await db.commit()
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invitation has expired")

        # Check existing member
        existing = await self.repo.get_membership(db, invite.organization_id, user.id)
        if not existing:
            member = OrganizationMember(
                organization_id=invite.organization_id,
                user_id=user.id,
                role=invite.role,
                status="active"
            )
            await self.repo.add_member(db, member)

            # Auto-add user to default workspace of this org
            ws_stmt = select(Workspace).where(Workspace.organization_id == invite.organization_id, Workspace.is_default == True)
            ws_res = await db.execute(ws_stmt)
            def_ws = ws_res.scalar_one_or_none()
            if def_ws:
                ws_service = WorkspaceService(db)
                await ws_service.invite_workspace_member(def_ws.id, invite.organization_id, user.id, invite.role)

        invite.status = "accepted"
        user.current_organization_id = invite.organization_id
        db.add(user)

        # Mark associated notifications as read
        try:
            from ..notifications.service import NotificationService
            notif_service = NotificationService(db)
            await notif_service.mark_read_by_entity(user.id, "organization_invitation", invite.id)
        except Exception as e:
            logger.warning(f"Failed to resolve notification for accepted invite: {e}")

        await db.commit()
        return {"status": "ok", "message": "Invitation accepted successfully", "organization_id": str(invite.organization_id)}

    async def reject_invitation(self, db: AsyncSession, invite_id: UUID, user: User) -> dict:
        invite = await self.repo.get_invitation_by_id(db, invite_id)
        if not invite or invite.email != user.email:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invitation not found")

        invite.status = "rejected"

        # Mark associated notifications as read
        try:
            from ..notifications.service import NotificationService
            notif_service = NotificationService(db)
            await notif_service.mark_read_by_entity(user.id, "organization_invitation", invite.id)
        except Exception as e:
            logger.warning(f"Failed to resolve notification for rejected invite: {e}")

        await db.commit()
        return {"status": "ok", "message": "Invitation rejected"}

    async def switch_organization(self, db: AsyncSession, org_id: UUID, user: User) -> Organization:
        membership = await self.repo.get_membership(db, org_id, user.id)
        if not membership:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You are not a member of this organization")

        org = await self.get_organization(db, org_id)
        user.current_organization_id = org.id

        # Find workspace in new org
        ws_stmt = select(Workspace).where(Workspace.organization_id == org.id, Workspace.deleted_at == None).order_by(Workspace.is_default.desc())
        ws_res = await db.execute(ws_stmt)
        workspaces = list(ws_res.scalars().all())

        if workspaces:
            user.current_workspace_id = workspaces[0].id

        db.add(user)
        await db.commit()
        return org

    async def leave_organization(self, db: AsyncSession, org_id: UUID, user: User) -> None:
        org = await self.get_organization(db, org_id)
        if org.owner_id == user.id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Organization owner cannot leave the organization. Transfer ownership or delete the organization.")

        membership = await self.repo.get_membership(db, org_id, user.id)
        if not membership:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Membership not found")

        await self.repo.remove_member(db, membership)

        # Re-assign active org if current
        if user.current_organization_id == org_id:
            remaining = await self.repo.list_user_organizations(db, user.id)
            if remaining and remaining[0].organization:
                user.current_organization_id = remaining[0].organization.id
            else:
                user.current_organization_id = None
            db.add(user)

        await db.commit()

    async def remove_member(self, db: AsyncSession, org_id: UUID, member_user_id: UUID) -> None:
        member = await self.repo.get_membership(db, org_id, member_user_id)
        if not member:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Member not found")
        await self.repo.remove_member(db, member)
        await db.commit()

    async def change_role(self, db: AsyncSession, org_id: UUID, member_user_id: UUID, role_name: str) -> OrganizationMember:
        member = await self.repo.get_membership(db, org_id, member_user_id)
        if not member:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Member not found")

        member.role = role_name.lower()
        await db.commit()
        await db.refresh(member)
        return member

    async def list_members(self, db: AsyncSession, org_id: UUID) -> List[dict]:
        memberships = await self.repo.list_memberships(db, org_id)
        roster = []
        for m in memberships:
            if m.user:
                roster.append({
                    "user_id": m.user.id,
                    "username": m.user.username,
                    "email": m.user.email,
                    "first_name": m.user.first_name,
                    "last_name": m.user.last_name,
                    "avatar_url": m.user.avatar_url,
                    "role": m.role or "member",
                    "status": m.status or "active",
                    "joined_at": m.joined_at or m.created_at
                })
        return roster

