import logging
import time
from typing import Any, Dict
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.agent import Agent as DBAgent
from app.agents.context import SessionContext
from app.agents.exceptions import PermissionDeniedException, AgentException
from app.agents.permissions import AgentPermissionValidator
from app.agents.loader import AgentLoader
from app.agents.sdk.session import AgentSession
from app.agents.sdk.memory import AgentMemory
from app.agents.metrics import metrics_tracker

logger = logging.getLogger(__name__)

class AgentExecutionEngine:
    @staticmethod
    async def get_or_create_db_agent(db: AsyncSession, name: str, org_id: UUID) -> DBAgent:
        """Finds or creates a database record for code-based agents to support long-term memory."""
        stmt = select(DBAgent).where(
            DBAgent.name == name,
            DBAgent.organization_id == org_id
        )
        res = await db.execute(stmt)
        db_agent = res.scalar_one_or_none()

        if not db_agent:
            db_agent = DBAgent(
                name=name,
                role="System Agent",
                system_prompt=f"You are a system-defined {name}.",
                organization_id=org_id
            )
            db.add(db_agent)
            await db.commit()
            await db.refresh(db_agent)
        return db_agent

    @staticmethod
    async def run(
        agent_id: str,
        context: SessionContext,
        input_data: Dict[str, Any],
        db: AsyncSession
    ) -> Dict[str, Any]:
        """Runs the agent execution pipeline."""
        start_time = time.time()
        
        # 1. Check basic context permissions (tenant, workspace, project isolation)
        await AgentPermissionValidator.validate_context_access(db, context)

        # 2. Resolve & Load Agent
        agent_inst = await AgentLoader.load_agent_instance(agent_id, db)

        # 3. Check agent-level permissions
        if agent_inst.required_permissions:
            is_allowed = await AgentPermissionValidator.validate_tool_permission(
                db, context, agent_inst.required_permissions
            )
            if not is_allowed:
                raise PermissionDeniedException(
                    f"Agent '{agent_inst.name}' requires permissions {agent_inst.required_permissions} which this context lacks."
                )

        # 4. Resolve DB UUID for code-based agents
        try:
            agent_uuid = UUID(agent_inst.agent_id)
        except ValueError:
            # Code-based agent, resolve/create DB reference
            db_agent = await AgentExecutionEngine.get_or_create_db_agent(
                db, agent_inst.name, context.organization_id
            )
            agent_uuid = db_agent.id
            agent_inst.agent_id = str(db_agent.id)

        # 5. Initialize session and inject memory/logger helpers
        session = AgentSession(context)
        session.status = "RUNNING"
        session.log("INFO", f"Loaded agent '{agent_inst.name}' version {agent_inst.version}")

        # Inject memory service for the agent to access
        agent_memory = AgentMemory(agent_uuid, context.organization_id, db)
        setattr(agent_inst, "memory", agent_memory)

        try:
            # 6. Planning phase
            session.log("INFO", "Running agent planning hook...")
            plan_res = await agent_inst.plan(context, input_data)
            session.log("INFO", f"Plan generated: {plan_res}")

            # 7. Validation phase
            session.log("INFO", "Running validation hook...")
            is_valid = await agent_inst.validate(context, input_data)
            if not is_valid:
                raise AgentException("Validation hook failed: inputs are not valid for this agent execution.")

            # 8. Main execution phase
            session.log("INFO", "Executing agent...")
            result = await agent_inst.execute(context, input_data, db)
            session.complete(result)
            session.log("INFO", "Execution completed successfully.")

            # Record success metrics
            duration_ms = (time.time() - start_time) * 1000.0
            metrics_tracker.record_execution(
                agent_id=agent_inst.name,
                duration_ms=duration_ms,
                success=True
            )

            return {
                "status": "success",
                "agent": {
                    "id": agent_inst.agent_id,
                    "name": agent_inst.name,
                    "version": agent_inst.version
                },
                "session_id": session.session_id,
                "plan": plan_res,
                "result": result,
                "duration_ms": round(duration_ms, 2)
            }

        except Exception as e:
            session.fail(e)
            session.log("ERROR", f"Agent execution failed with error: {str(e)}")
            
            # Record failure metrics
            duration_ms = (time.time() - start_time) * 1000.0
            metrics_tracker.record_execution(
                agent_id=agent_inst.name,
                duration_ms=duration_ms,
                success=False
            )
            
            raise
        finally:
            # 9. Cleanup phase
            try:
                await agent_inst.cleanup(context)
            except Exception as e_clean:
                logger.error(f"Error during agent cleanup: {str(e_clean)}", exc_info=True)
