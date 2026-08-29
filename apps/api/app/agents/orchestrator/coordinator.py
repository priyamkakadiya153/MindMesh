import logging
from typing import List, Dict, Any, Callable, Awaitable
from app.agents.execution.graph import AgentExecutionNode
from app.agents.execution.parallel import ParallelExecutor
from app.agents.execution.sequential import SequentialExecutor
from app.agents.collaboration.consensus import ConsensusFramework
from app.agents.collaboration.conflict import ConflictResolver

logger = logging.getLogger(__name__)

class CollaborationCoordinator:
    @staticmethod
    async def coordinate_sequential(
        nodes: List[AgentExecutionNode],
        execution_func: Callable[[AgentExecutionNode], Awaitable[None]]
    ):
        """Coordinates sequential pipeline execution."""
        await SequentialExecutor.execute_sequential(nodes, execution_func)

    @staticmethod
    async def coordinate_parallel(
        nodes: List[AgentExecutionNode],
        execution_func: Callable[[AgentExecutionNode], Awaitable[None]]
    ):
        """Coordinates concurrent batch execution."""
        await ParallelExecutor.execute_parallel(nodes, execution_func)

    @staticmethod
    async def coordinate_consensus(
        nodes: List[AgentExecutionNode],
        execution_func: Callable[[AgentExecutionNode], Awaitable[None]],
        match_key: str = "status"
    ) -> Dict[str, Any]:
        """Runs redundant executions of multiple nodes and resolves conflicts if any."""
        logger.info(f"CollaborationCoordinator: Running consensus verification for {len(nodes)} redundant step(s).")
        
        # 1. Run all nodes in parallel
        await ParallelExecutor.execute_parallel(nodes, execution_func)

        # 2. Extract output payloads
        outputs = [node.result for node in nodes if node.status == "COMPLETED" and node.result]
        
        # 3. Check majority consensus
        res = ConsensusFramework.verify_consensus(outputs, match_key=match_key)
        if res["consensus"]:
            logger.info("CollaborationCoordinator: Majority consensus reached.")
            return res["output"]

        # 4. Resolve conflict if majority not found
        logger.warning("CollaborationCoordinator: Consensus failed. Resolving output conflict.")
        resolution = ConflictResolver.resolve(outputs, match_key=match_key)
        return resolution["output"]
