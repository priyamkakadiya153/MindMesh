import logging
from uuid import UUID
from typing import List, Optional, Dict, Any
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.memory.models import GovernancePolicy

logger = logging.getLogger(__name__)

class PolicyStore:
    @staticmethod
    async def create_policy(
        db: AsyncSession,
        organization_id: UUID,
        name: str,
        category: str,
        rules: Dict[str, Any]
    ) -> GovernancePolicy:
        """Saves a governance policy block."""
        policy = GovernancePolicy(
            organization_id=organization_id,
            name=name,
            category=category,
            rules=rules,
            is_active=True
        )
        db.add(policy)
        await db.flush()
        logger.info(f"PolicyStore: Created category '{category}' policy '{name}' for org '{organization_id}'")
        return policy

    @staticmethod
    async def get_policy(db: AsyncSession, policy_id: UUID) -> Optional[GovernancePolicy]:
        stmt = select(GovernancePolicy).where(GovernancePolicy.id == policy_id)
        res = await db.execute(stmt)
        return res.scalar_one_or_none()

    @staticmethod
    async def list_policies(
        db: AsyncSession,
        organization_id: UUID,
        category: Optional[str] = None
    ) -> List[GovernancePolicy]:
        """Lists active organizational policies."""
        stmt = select(GovernancePolicy).where(
            GovernancePolicy.organization_id == organization_id,
            GovernancePolicy.is_active == True
        )
        if category:
            stmt = stmt.where(GovernancePolicy.category == category)
            
        res = await db.execute(stmt)
        return list(res.scalars().all())
