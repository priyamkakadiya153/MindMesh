from app.agents.events import agent_events
from app.agents.execution.graph import AgentExecutionNode

class OrchestratorEvents:
    @staticmethod
    async def team_started(execution_id: str, supervisor_name: str):
        await agent_events.trigger("team_started", {
            "execution_id": execution_id,
            "supervisor": supervisor_name
        })

    @staticmethod
    async def delegation_triggered(node_id: str, agent_name: str):
        await agent_events.trigger("delegation_triggered", {
            "node_id": node_id,
            "agent": agent_name
        })

    @staticmethod
    async def conflict_detected(node_id: str):
        await agent_events.trigger("conflict_detected", {
            "node_id": node_id
        })
