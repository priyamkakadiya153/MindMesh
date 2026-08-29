from app.agents.events import agent_events
from app.agents.planning.graph import ExecutionNode

class ExecutionEvents:
    @staticmethod
    async def step_started(node: ExecutionNode):
        await agent_events.trigger("step_started", {
            "node_id": node.id,
            "tool": node.tool,
            "input": node.input
        })

    @staticmethod
    async def step_completed(node: ExecutionNode):
        await agent_events.trigger("step_completed", {
            "node_id": node.id,
            "tool": node.tool,
            "result": node.result
        })

    @staticmethod
    async def step_failed(node: ExecutionNode, error: str):
        await agent_events.trigger("step_failed", {
            "node_id": node.id,
            "tool": node.tool,
            "error": error
        })
