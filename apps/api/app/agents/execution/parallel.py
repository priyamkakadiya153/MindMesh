import asyncio
import logging
from typing import List, Callable, Awaitable
from app.agents.execution.graph import AgentExecutionNode

logger = logging.getLogger(__name__)

class ParallelExecutor:
    @staticmethod
    async def execute_parallel(
        nodes: List[AgentExecutionNode],
        execution_func: Callable[[AgentExecutionNode], Awaitable[None]]
    ):
        """Runs multiple agent execution nodes concurrently."""
        logger.info(f"ParallelExecutor: Dispatching {len(nodes)} agent step(s) concurrently.")
        tasks = [execution_func(node) for node in nodes]
        await asyncio.gather(*tasks)
