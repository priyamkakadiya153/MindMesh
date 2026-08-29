from uuid import UUID
from typing import Dict, Any, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.agent import AgentMemory as DBAgentMemory

class AgentMemory:
    def __init__(self, agent_id: UUID, organization_id: UUID, db: AsyncSession):
        self.agent_id = agent_id
        self.organization_id = organization_id
        self.db = db
        self._short_term: Dict[str, Any] = {}

    def get_short_term(self, key: str, default: Any = None) -> Any:
        """Fetch value from short-term (in-session) memory."""
        return self._short_term.get(key, default)

    def set_short_term(self, key: str, value: Any):
        """Save value to short-term (in-session) memory."""
        self._short_term[key] = value

    async def get_long_term(self) -> Dict[str, Any]:
        """Loads persistent JSON context data from database."""
        stmt = select(DBAgentMemory).where(
            DBAgentMemory.agent_id == self.agent_id,
            DBAgentMemory.organization_id == self.organization_id
        )
        res = await self.db.execute(stmt)
        mem_row = res.scalar_one_or_none()
        if mem_row and mem_row.context_data:
            return mem_row.context_data
        return {}

    async def save_long_term(self, context_data: Dict[str, Any]):
        """Persists or updates JSON context data in database."""
        stmt = select(DBAgentMemory).where(
            DBAgentMemory.agent_id == self.agent_id,
            DBAgentMemory.organization_id == self.organization_id
        )
        res = await self.db.execute(stmt)
        mem_row = res.scalar_one_or_none()

        if mem_row:
            # Overwrite or merge
            mem_row.context_data = context_data
        else:
            mem_row = DBAgentMemory(
                agent_id=self.agent_id,
                organization_id=self.organization_id,
                context_data=context_data
            )
            self.db.add(mem_row)

        await self.db.commit()
