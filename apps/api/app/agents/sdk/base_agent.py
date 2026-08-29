from abc import ABC, abstractmethod
from typing import Any, Dict, List
from sqlalchemy.ext.asyncio import AsyncSession
from app.agents.context import SessionContext

class BaseAgent(ABC):
    def __init__(
        self,
        agent_id: str = None,
        name: str = None,
        description: str = None,
        version: str = "1.0.0",
        required_permissions: List[str] = None
    ):
        self.agent_id = agent_id
        self.name = name
        self.description = description
        self.version = version
        self.required_permissions = required_permissions or []

    @abstractmethod
    async def execute(self, context: SessionContext, input_data: Dict[str, Any], db: AsyncSession) -> Dict[str, Any]:
        """Core execution logic of the agent."""
        pass

    async def plan(self, context: SessionContext, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Optional task decomposition/planning logic. Defaults to a single step."""
        return {"plan": f"Execute agent '{self.name}' version {self.version} sequentially."}

    async def validate(self, context: SessionContext, input_data: Dict[str, Any]) -> bool:
        """Validates parameters before execution. Defaults to True."""
        return True

    async def cleanup(self, context: SessionContext) -> None:
        """Resource cleanup hook after execution completes."""
        pass
