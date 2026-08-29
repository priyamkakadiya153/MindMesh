import asyncio
import logging
import re
from typing import Dict, Any, List
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from app.agents.context import SessionContext
from app.agents.planning.graph import ExecutionGraph, ExecutionNode
from app.agents.tool_calling.dispatcher import ToolDispatcher
from app.agents.reasoning.reflection import ReflectionEngine
from app.agents.reasoning.recovery import RecoveryEngine
from app.agents.reasoning.constraints import ConstraintValidator
from app.agents.execution.retries import RetryPolicy
from app.agents.execution.rollback import RollbackManager, rollback_created_project, rollback_created_task
from app.agents.execution.audit import ExecutionAuditLogger
from app.agents.execution.events import ExecutionEvents
from app.agents.exceptions import AgentException

logger = logging.getLogger(__name__)

class GraphOrchestrator:
    def __init__(self, graph: ExecutionGraph):
        self.graph = graph
        self.rollback_manager = RollbackManager()
        self.results: Dict[str, Any] = {}
        self.execution_count = 0

    def resolve_dynamic_inputs(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Resolves placeholders matching ${step_id.result.field} recursively."""
        
        def resolve_val(val: Any) -> Any:
            if isinstance(val, str):
                # 1. Exact match e.g. ${step_1.result.id}
                match = re.match(r"\$\{\s*([a-zA-Z0-9_-]+)\.result\.([a-zA-Z0-9_-]+)\s*\}", val)
                if match:
                    step_id = match.group(1)
                    field_name = match.group(2)
                    step_res = self.results.get(step_id)
                    if step_res and isinstance(step_res, dict):
                        return step_res.get(field_name)
                    return val
                
                # 2. Substring match
                sub_matches = re.findall(r"\$\{\s*([a-zA-Z0-9_-]+)\.result\.([a-zA-Z0-9_-]+)\s*\}", val)
                for step_id, field_name in sub_matches:
                    step_res = self.results.get(step_id)
                    if step_res and isinstance(step_res, dict):
                        resolved = step_res.get(field_name, "")
                        val = val.replace(f"${{{step_id}.result.{field_name}}}", str(resolved))
                return val
            elif isinstance(val, dict):
                return {k: resolve_val(v) for k, v in val.items()}
            elif isinstance(val, list):
                return [resolve_val(item) for item in val]
            return val

        return resolve_val(inputs)

    async def execute_node(self, node: ExecutionNode, context: SessionContext, db: AsyncSession):
        """Executes a single graph node with metrics, retries, and rollback registration."""
        self.execution_count += 1
        ConstraintValidator.check_loop_limit(self.execution_count)

        node.status = "RUNNING"
        await ExecutionEvents.step_started(node)

        # 1. Resolve dynamic outputs injected from dependent tasks
        resolved_inputs = self.resolve_dynamic_inputs(node.input)

        async def run_dispatch():
            return await ToolDispatcher.dispatch(node.tool, resolved_inputs, context, db)

        try:
            # 2. Run with RetryPolicy
            result = await RetryPolicy.execute_with_retry(
                run_dispatch,
                retries=1, # simple count for tests, can scale
                initial_delay=0.01
            )

            # 3. Reflection verification
            reflection = ReflectionEngine.evaluate(node.tool, result)
            if not reflection["success"]:
                raise ValueError(f"Reflection check failed: {reflection['missing_data']}")

            # Save result state
            node.status = "COMPLETED"
            node.result = result
            self.results[node.id] = result
            
            await ExecutionEvents.step_completed(node)
            await ExecutionAuditLogger.log_step(
                db, context, node.id, node.tool, "COMPLETED", {"result": result}
            )

            # 4. Register compensations for database changes
            if node.tool == "create_project" and result and "id" in result:
                self.rollback_manager.register_rollback(
                    node.id, rollback_created_project, UUID(result["id"]), db
                )
            elif node.tool == "create_task" and result and "id" in result:
                self.rollback_manager.register_rollback(
                    node.id, rollback_created_task, UUID(result["id"]), db
                )

        except Exception as e:
            logger.error(f"Orchestrator: Node '{node.id}' failed: {str(e)}")
            node.error = str(e)
            node.retries += 1
            
            # 5. Recovery Strategy check
            strategy = RecoveryEngine.determine_strategy(node, max_retries=2)
            
            if strategy == "RETRY":
                node.status = "PENDING"  # resets to retry on next loop
            elif strategy == "ALTERNATIVE":
                # Fallback to alternate tool
                alternatives = {
                    "search_documents": "retrieve_knowledge"
                }
                node.tool = alternatives.get(node.tool, "search_documents")
                node.retries = 0  # reset retries for the alternative tool
                node.status = "PENDING"
            else:
                # ABORT/ESCALATE: Rollback all completed steps
                node.status = "FAILED"
                await ExecutionEvents.step_failed(node, str(e))
                await ExecutionAuditLogger.log_step(
                    db, context, node.id, node.tool, "FAILED", {"error": str(e)}
                )
                await self.rollback_manager.rollback()
                raise AgentException(f"Graph execution failed on step '{node.id}': {str(e)}")

    async def execute(self, context: SessionContext, db: AsyncSession) -> Dict[str, Any]:
        """Orchestrates execution loop for ready DAG nodes."""
        logger.info(f"Orchestrator: Starting graph execution for request {context.request_id}")
        
        while True:
            ready_nodes = self.graph.get_ready_nodes()
            if not ready_nodes:
                # Loop until complete or blocked
                if self.graph.is_completed():
                    logger.info("Orchestrator: Graph execution completed successfully.")
                    break
                elif self.graph.is_failed():
                    raise AgentException("Orchestrator: Graph execution failed.")
                else:
                    # Deadlock check: uncompleted nodes remain but none are ready (cyclic or missing dependencies)
                    uncompleted = [n.id for n in self.graph.nodes.values() if n.status != "COMPLETED"]
                    if uncompleted:
                        logger.error(f"Orchestrator: Deadlock or incomplete dependencies detected. Steps left: {uncompleted}")
                        for nid in uncompleted:
                            self.graph.nodes[nid].status = "FAILED"
                        await self.rollback_manager.rollback()
                        raise AgentException(f"Deadlock detected: uncompleted steps {uncompleted} could not be scheduled.")
                    break

            # Execute all ready nodes in parallel batches
            logger.info(f"Orchestrator: Scheduling batch of {len(ready_nodes)} parallel node(s)")
            tasks = [self.execute_node(node, context, db) for node in ready_nodes]
            await asyncio.gather(*tasks)

        return self.results
