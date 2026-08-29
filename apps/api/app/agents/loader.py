from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.agent import Agent as DBAgent
from app.agents.registry import agent_registry
from app.agents.sdk.base_agent import BaseAgent
from app.agents.exceptions import AgentNotFoundException
from app.agents.context import SessionContext
from typing import Dict, Any

class GenericDBAgent(BaseAgent):
    def __init__(self, db_agent: DBAgent):
        super().__init__(
            agent_id=str(db_agent.id),
            name=db_agent.name,
            description=f"Generic DB Agent running as {db_agent.role}",
            version="1.0.0",
            required_permissions=[]
        )
        self.role = db_agent.role
        self.system_prompt = db_agent.system_prompt

    async def execute(self, context: SessionContext, input_data: Dict[str, Any], db: AsyncSession) -> Dict[str, Any]:
        """Runs the generic DB agent logic, which returns execution summary."""
        return {
            "agent_id": self.agent_id,
            "name": self.name,
            "role": self.role,
            "system_prompt": self.system_prompt,
            "input_received": input_data,
            "status": "executed"
        }

class AgentLoader:
    @staticmethod
    async def load_agent_instance(agent_id_str: str, db: AsyncSession) -> BaseAgent:
        """Resolves and loads agent class from registry or database."""
        # 1. Check registry (code-based agent)
        agent_cls = agent_registry.get_agent(agent_id_str)
        if not agent_cls:
            normalized_id = agent_id_str.lower().replace("agent", "")
            agent_cls = agent_registry.get_agent(normalized_id)
        if agent_cls:
            # Check meta to determine if it defines custom config
            meta = getattr(agent_cls, "_agent_meta", {})
            name = meta.get("name", agent_cls.__name__)
            required_permissions = meta.get("required_permissions", [])
            version = meta.get("version", "1.0.0")

            inst = agent_cls()
            # If the instance lacks standard properties, populate them
            if not hasattr(inst, "agent_id") or not inst.agent_id:
                inst.agent_id = agent_id_str
            if not hasattr(inst, "name") or not inst.name:
                inst.name = name
            if not hasattr(inst, "description") or not inst.description:
                inst.description = meta.get("description", "")
            if not hasattr(inst, "version") or not inst.version:
                inst.version = version
            if not hasattr(inst, "required_permissions") or not inst.required_permissions:
                inst.required_permissions = required_permissions
            return inst

        # 2. Check Database (generic DB agent)
        try:
            agent_uuid = UUID(agent_id_str)
        except ValueError:
            raise AgentNotFoundException(
                f"Agent '{agent_id_str}' is not registered and is not a valid UUID."
            )

        stmt = select(DBAgent).where(DBAgent.id == agent_uuid)
        res = await db.execute(stmt)
        db_agent = res.scalar_one_or_none()
        if not db_agent:
            raise AgentNotFoundException(f"Agent with ID {agent_id_str} was not found in database.")

        return GenericDBAgent(db_agent)
