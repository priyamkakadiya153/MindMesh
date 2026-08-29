import logging
from typing import List, Callable, Awaitable, Dict, Any
from app.agents.execution.graph import AgentExecutionNode

logger = logging.getLogger(__name__)

class SequentialExecutor:
    @staticmethod
    async def execute_sequential(
        nodes: List[AgentExecutionNode],
        execution_func: Callable[[AgentExecutionNode], Awaitable[None]]
    ):
        """Runs agent execution nodes in sequence, piping outputs forward."""
        logger.info(f"SequentialExecutor: Dispatching {len(nodes)} agent step(s) sequentially.")
        
        last_result: Dict[str, Any] = {}
        
        for node in nodes:
            # Inject outputs from previous steps
            if last_result:
                node.input_data.update({"parent_result": last_result})
                
            await execution_func(node)
            
            if node.result:
                last_result = node.result
