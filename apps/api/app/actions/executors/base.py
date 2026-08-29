from abc import ABC, abstractmethod
from typing import Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.user import User
from ..types import ActionProposal, ActionResult

class BaseActionExecutor(ABC):
    """Abstract Base Class for all MindMesh Action Executors."""

    @abstractmethod
    async def execute(
        self,
        proposal: ActionProposal,
        user: User,
        db: AsyncSession
    ) -> ActionResult:
        """Executes the action mutation against the database and returns ActionResult."""
        pass
