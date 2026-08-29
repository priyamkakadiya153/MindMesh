import logging
import re
import time
import uuid
import asyncio
from typing import Dict, Any, List, Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from app.agents.context import SessionContext
from app.agents.execution.graph import AgentExecutionGraph, AgentExecutionNode
from app.agents.execution.branching import BranchingManager
from app.agents.execution.rollback import MultiAgentRollbackTracker
from app.agents.execution.recovery import MultiAgentRecoveryLoop
from app.agents.collaboration.delegation import DelegationEngine
from app.agents.collaboration.aggregation import ResultAggregator
from app.agents.collaboration.consensus import ConsensusFramework
from app.agents.collaboration.conflict import ConflictResolver
from app.agents.orchestrator.dispatcher import MultiAgentDispatcher
from app.agents.orchestrator.scheduler import MultiAgentScheduler
from app.agents.orchestrator.lifecycle import agent_lifecycle
from app.agents.orchestrator.metrics import orchestration_metrics
from app.agents.orchestrator.events import OrchestratorEvents
from app.agents.exceptions import AgentException

logger = logging.getLogger(__name__)

class SupervisorAgent:
    def __init__(self):
        self.rollback_tracker = MultiAgentRollbackTracker()
        self.results: Dict[str, Any] = {}
        self.db_lock = asyncio.Lock()

    def plan_execution(self, goal: str, workspace_id: Optional[str] = None) -> AgentExecutionGraph:
        """Decomposes a user goal into an AgentExecutionGraph."""
        graph = AgentExecutionGraph()
        
        # Build rule-based plan depending on goal keywords
        goal_lower = goal.lower()
        
        # Scenario 1: Consensus testing goal
        if "consensus" in goal_lower or "validate" in goal_lower:
            graph.add_node(AgentExecutionNode(
                id="step_1",
                agent_name="ResearchAgent",
                input_data={"query": "Consensus consensus details"},
                dependencies=[]
            ))
            # Parallel nodes for consensus checks
            graph.add_node(AgentExecutionNode(
                id="step_check_a",
                agent_name="ComplianceAgent",
                input_data={"status": "APPROVED", "parent_result": "${step_1.result}"},
                dependencies=["step_1"]
            ))
            graph.add_node(AgentExecutionNode(
                id="step_check_b",
                agent_name="ComplianceAgent",
                input_data={"status": "APPROVED", "parent_result": "${step_1.result}"},
                dependencies=["step_1"]
            ))
            return graph

        # Scenario 2: Default reporting or custom project creation goal
        graph.add_node(AgentExecutionNode(
            id="step_1",
            agent_name="PlannerAgent",
            input_data={"name": "Engineering Q1 Project"},
            dependencies=[]
        ))
        
        task_input = {"description": "Prepare Specs"}
        if workspace_id:
            task_input["workspace_id"] = workspace_id
        
        graph.add_node(AgentExecutionNode(
            id="step_2",
            agent_name="ResearchAgent",
            input_data=task_input,
            dependencies=["step_1"]
        ))
        
        graph.add_node(AgentExecutionNode(
            id="step_3",
            agent_name="ReportingAgent",
            input_data={"parent_data": "${step_2.result}"},
            dependencies=["step_2"]
        ))
        
        return graph

    def resolve_placeholders(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Resolves output placeholder values dynamically from previous steps."""
        def resolve_val(val: Any) -> Any:
            if isinstance(val, str):
                match = re.match(r"\$\{\s*([a-zA-Z0-9_-]+)\.result\s*\}", val)
                if match:
                    step_id = match.group(1)
                    return self.results.get(step_id, val)
                
                # Check for nested keys, e.g. ${step_1.result.id}
                match_nested = re.match(r"\$\{\s*([a-zA-Z0-9_-]+)\.result\.([a-zA-Z0-9_-]+)\s*\}", val)
                if match_nested:
                    step_id = match_nested.group(1)
                    field_name = match_nested.group(2)
                    step_res = self.results.get(step_id)
                    if step_res and isinstance(step_res, dict):
                        return step_res.get(field_name, val)
                return val
            elif isinstance(val, dict):
                return {k: resolve_val(v) for k, v in val.items()}
            elif isinstance(val, list):
                return [resolve_val(item) for item in val]
            return val

        return resolve_val(inputs)

    async def execute_node(self, node: AgentExecutionNode, context: SessionContext, db: AsyncSession):
        """Executes a single agent node with metric, retries, and rollback capabilities."""
        node.status = "RUNNING"
        
        # 1. Dynamic delegation check
        # If agent_name is unassigned or generic, resolve it dynamically
        if not node.agent_name:
            node.agent_name = DelegationEngine.delegate_task(node.id)
            await OrchestratorEvents.delegation_triggered(node.id, node.agent_name)

        orchestration_metrics.record_agent_call(node.agent_name)

        # 2. Resolve placeholders from previous steps
        node.input_data = self.resolve_placeholders(node.input_data)

        # 3. Execute with recovery loop
        try:
            async with self.db_lock:
                res = await MultiAgentDispatcher.dispatch_to_agent(node, context, db)
            node.status = "COMPLETED"
            node.result = res
            self.results[node.id] = res

            # Handle conditional paths checking
            BranchingManager.evaluate_branches(node, self.graph_ref)

        except Exception as e:
            logger.error(f"SupervisorAgent: Step '{node.id}' failed with: {str(e)}")
            node.error = str(e)
            
            strategy = MultiAgentRecoveryLoop.determine_recovery(node, max_retries=1)
            if strategy == "RETRY":
                node.status = "PENDING"
            elif strategy == "RE_DELEGATE":
                # Rescheduled with alternative agent
                node.status = "PENDING"
                await OrchestratorEvents.delegation_triggered(node.id, node.agent_name)
            else:
                node.status = "FAILED"
                await self.rollback_tracker.execute_rollback()
                raise AgentException(f"SupervisorAgent: Multi-agent execution aborted on step '{node.id}': {str(e)}")

    async def run_workflow(self, goal: str, context: SessionContext, db: AsyncSession) -> Dict[str, Any]:
        """Runs the complete multi-agent orchestrator loop."""
        start_time = time.time()
        execution_id = context.request_id or str(uuid.uuid4())
        
        # Register in lifecycle tracker
        agent_lifecycle.register_team(execution_id, "SupervisorAgent")
        await OrchestratorEvents.team_started(execution_id, "SupervisorAgent")

        # 1. Generate execution plan graph
        graph = self.plan_execution(goal, workspace_id=str(context.workspace_id) if context.workspace_id else None)
        self.graph_ref = graph

        # 2. Assign dynamic agents
        for node in graph.nodes.values():
            if not node.agent_name:
                node.agent_name = DelegationEngine.delegate_task(node.id)

        # 3. Execution loop
        while True:
            ready_nodes = graph.get_ready_nodes()
            if not ready_nodes:
                if graph.is_completed():
                    break
                elif graph.is_failed():
                    raise AgentException("SupervisorAgent: Workflow failed.")
                else:
                    # Deadlock check
                    uncompleted = [n.id for n in graph.nodes.values() if n.status != "COMPLETED"]
                    if uncompleted:
                        await self.rollback_tracker.execute_rollback()
                        raise AgentException(f"SupervisorAgent: Deadlock occurred. Incomplete steps: {uncompleted}")
                    break

            # 4. Schedule nodes based on priority or load
            scheduled = MultiAgentScheduler.schedule_nodes(ready_nodes, policy="priority-based")

            # Check if this is a consensus step
            is_consensus_batch = all(n.agent_name == "ComplianceAgent" for n in scheduled) and len(scheduled) > 1
            
            if is_consensus_batch:
                orchestration_metrics.record_consensus()
                # Run consensus check
                tasks = [self.execute_node(n, context, db) for n in scheduled]
                await asyncio.gather(*tasks)

                outputs = [n.result for n in scheduled if n.status == "COMPLETED" and n.result]
                consensus_res = ConsensusFramework.verify_consensus(outputs, match_key="status")
                
                if not consensus_res["consensus"]:
                    await OrchestratorEvents.conflict_detected(scheduled[0].id)
                    orchestration_metrics.record_conflict()
                    resolved_payload = ConflictResolver.resolve(outputs, match_key="status")
                    consensus_output = resolved_payload
                else:
                    consensus_output = consensus_res["output"]

                # Save merged result to a custom node if needed or map directly
                self.results["consensus_merge"] = consensus_output
            else:
                # Concurrently execute scheduled parallel batch nodes
                tasks = [self.execute_node(n, context, db) for n in scheduled]
                await asyncio.gather(*tasks)

        # 5. Aggregate final results
        final_list = [self.results[nid] for nid in graph.nodes.keys() if nid in self.results]
        aggregated = ResultAggregator.aggregate_results(final_list)

        # Track coordination metrics
        latency_ms = (time.time() - start_time) * 1000.0
        orchestration_metrics.record_coordination(latency_ms)
        agent_lifecycle.teardown_team(execution_id, success=True)

        return {
            "execution_id": execution_id,
            "status": "COMPLETED",
            "goal": goal,
            "aggregated_output": aggregated,
            "metrics": orchestration_metrics.get_summary()
        }
