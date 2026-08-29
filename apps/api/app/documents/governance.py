from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from .models import RetentionPolicy, Document
from .exceptions import InvalidFileException

class GovernanceService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_or_create_retention_policy(
        self,
        org_id: UUID,
        name: str = "Default Retention Policy",
        retention_days: int = 365,
        auto_archive: bool = True,
        auto_delete: bool = False
    ) -> RetentionPolicy:
        stmt = select(RetentionPolicy).where(RetentionPolicy.organization_id == org_id)
        policy = (await self.db.execute(stmt)).scalar_one_or_none()
        
        if not policy:
            policy = RetentionPolicy(
                organization_id=org_id,
                name=name,
                retention_days=retention_days,
                auto_archive=auto_archive,
                auto_delete=auto_delete
            )
            self.db.add(policy)
            await self.db.flush()
            
        return policy

    async def update_retention_policy(
        self,
        org_id: UUID,
        retention_days: int,
        auto_archive: bool,
        auto_delete: bool
    ) -> RetentionPolicy:
        policy = await self.get_or_create_retention_policy(org_id)
        
        if retention_days < 1:
            raise InvalidFileException("Retention days must be at least 1.")
            
        policy.retention_days = retention_days
        policy.auto_archive = auto_archive
        policy.auto_delete = auto_delete
        
        await self.db.commit()
        return policy
