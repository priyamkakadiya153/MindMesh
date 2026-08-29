from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from uuid import UUID
from typing import List, Optional
from ..models.organization import Organization, OrganizationSettings, OrganizationInvitation
from ..models.organization_member import OrganizationMember

class OrganizationRepository:
    async def create_organization(self, db: AsyncSession, org: Organization) -> Organization:
        db.add(org)
        await db.flush()
        return await self.get_organization(db, org.id)

    async def get_organization(self, db: AsyncSession, org_id: UUID) -> Optional[Organization]:
        stmt = (
            select(Organization)
            .options(selectinload(Organization.settings))
            .where(Organization.id == org_id, Organization.deleted_at == None)
        )
        res = await db.execute(stmt)
        return res.scalar_one_or_none()

    async def get_organization_by_slug(self, db: AsyncSession, slug: str) -> Optional[Organization]:
        stmt = (
            select(Organization)
            .options(selectinload(Organization.settings))
            .where(Organization.slug == slug, Organization.deleted_at == None)
        )
        res = await db.execute(stmt)
        return res.scalar_one_or_none()

    async def list_user_organizations(self, db: AsyncSession, user_id: UUID) -> List[OrganizationMember]:
        stmt = (
            select(OrganizationMember)
            .options(selectinload(OrganizationMember.organization).selectinload(Organization.settings))
            .where(OrganizationMember.user_id == user_id, OrganizationMember.deleted_at == None)
        )
        res = await db.execute(stmt)
        return list(res.scalars().all())

    async def get_membership(self, db: AsyncSession, org_id: UUID, user_id: UUID) -> Optional[OrganizationMember]:
        stmt = (
            select(OrganizationMember)
            .options(selectinload(OrganizationMember.role_rel))
            .where(
                OrganizationMember.organization_id == org_id,
                OrganizationMember.user_id == user_id,
                OrganizationMember.deleted_at == None
            )
        )
        res = await db.execute(stmt)
        return res.scalar_one_or_none()

    async def list_memberships(self, db: AsyncSession, org_id: UUID) -> List[OrganizationMember]:
        stmt = (
            select(OrganizationMember)
            .options(selectinload(OrganizationMember.user))
            .where(OrganizationMember.organization_id == org_id, OrganizationMember.deleted_at == None)
        )
        res = await db.execute(stmt)
        return list(res.scalars().all())

    async def add_member(self, db: AsyncSession, member: OrganizationMember) -> OrganizationMember:
        db.add(member)
        await db.flush()
        return member

    async def remove_member(self, db: AsyncSession, member: OrganizationMember) -> None:
        await db.delete(member)
        await db.flush()

    async def get_settings(self, db: AsyncSession, org_id: UUID) -> Optional[OrganizationSettings]:
        stmt = select(OrganizationSettings).where(OrganizationSettings.organization_id == org_id)
        res = await db.execute(stmt)
        return res.scalar_one_or_none()

    async def save_settings(self, db: AsyncSession, settings: OrganizationSettings) -> OrganizationSettings:
        db.add(settings)
        await db.flush()
        return settings

    async def create_invitation(self, db: AsyncSession, invite: OrganizationInvitation) -> OrganizationInvitation:
        db.add(invite)
        await db.flush()
        return invite

    async def get_invitation_by_token(self, db: AsyncSession, token: str) -> Optional[OrganizationInvitation]:
        stmt = (
            select(OrganizationInvitation)
            .options(selectinload(OrganizationInvitation.organization))
            .where(OrganizationInvitation.token == token, OrganizationInvitation.deleted_at == None)
        )
        res = await db.execute(stmt)
        return res.scalar_one_or_none()

    async def get_invitation_by_id(self, db: AsyncSession, invite_id: UUID) -> Optional[OrganizationInvitation]:
        stmt = (
            select(OrganizationInvitation)
            .options(selectinload(OrganizationInvitation.organization))
            .where(OrganizationInvitation.id == invite_id, OrganizationInvitation.deleted_at == None)
        )
        res = await db.execute(stmt)
        return res.scalar_one_or_none()

    async def list_org_invitations(self, db: AsyncSession, org_id: UUID) -> List[OrganizationInvitation]:
        stmt = (
            select(OrganizationInvitation)
            .options(selectinload(OrganizationInvitation.organization))
            .where(OrganizationInvitation.organization_id == org_id, OrganizationInvitation.deleted_at == None)
            .order_by(OrganizationInvitation.created_at.desc())
        )
        res = await db.execute(stmt)
        return list(res.scalars().all())

    async def get_pending_invitation(self, db: AsyncSession, org_id: UUID, email: str) -> Optional[OrganizationInvitation]:
        stmt = (
            select(OrganizationInvitation)
            .options(selectinload(OrganizationInvitation.organization))
            .where(
                OrganizationInvitation.organization_id == org_id,
                OrganizationInvitation.email == email,
                OrganizationInvitation.status == "pending",
                OrganizationInvitation.deleted_at == None
            )
        )
        res = await db.execute(stmt)
        return res.scalar_one_or_none()

    async def list_user_invitations(self, db: AsyncSession, email: str) -> List[OrganizationInvitation]:
        stmt = (
            select(OrganizationInvitation)
            .options(selectinload(OrganizationInvitation.organization))
            .where(
                OrganizationInvitation.email == email,
                OrganizationInvitation.status == "pending",
                OrganizationInvitation.deleted_at == None
            )
            .order_by(OrganizationInvitation.created_at.desc())
        )
        res = await db.execute(stmt)
        return list(res.scalars().all())

