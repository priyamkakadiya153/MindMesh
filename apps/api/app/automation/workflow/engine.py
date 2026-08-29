import logging
import asyncio
from datetime import datetime
from typing import Dict, Any, List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.automation.approval.models import WorkflowExecution, WorkflowStepExecution, WorkflowDefinition
from app.automation.workflow.executor import WorkflowStepExecutor
from app.automation.workflow.lifecycle import WorkflowLifecycle
from app.automation.workflow.rollback import WorkflowRollbackCoordinator
from app.automation.workflow.metrics import WorkflowMetrics

logger = logging.getLogger(__name__)

class WorkflowEngine:
    @staticmethod
    async def resume_workflow(
        db: AsyncSession,
        execution: WorkflowExecution,
        completed_step_name: str,
        result: Dict[str, Any]
    ):
        """Resumes a paused workflow, marking the approval step complete and scheduling subsequent ready nodes."""
        logger.info(f"WorkflowEngine: Resuming execution '{execution.id}' after approval resolution of '{completed_step_name}'")
        
        # Locate step log
        stmt = select(WorkflowStepExecution).where(
            WorkflowStepExecution.execution_id == execution.id,
            WorkflowStepExecution.step_name == completed_step_name
        )
        res = await db.execute(stmt)
        step_log = res.scalar_one_or_none()

        if step_log:
            step_log.status = "Completed"
            step_log.completed_at = datetime.utcnow()
            step_log.duration_ms = WorkflowMetrics.calculate_duration_ms(step_log.started_at, step_log.completed_at)
            db.add(step_log)

        # Merge approval details into context
        context = dict(execution.context or {})
        context[completed_step_name] = {"result": result}
        execution.context = context
        execution.status = "Running"
        db.add(execution)
        await db.flush()

        # Resume the main execution loop
        await WorkflowEngine.execute_workflow(db, execution)

    @staticmethod
    def evaluate_condition(condition_str: str, context: Dict[str, Any]) -> bool:
        """Evaluates simple conditions e.g. '${status} == APPROVED'."""
        if not condition_str:
            return True
        try:
            # Resolve placeholders
            resolved = condition_str
            for key, val in context.items():
                placeholder = "${" + str(key) + "}"
                if placeholder in resolved:
                    resolved = resolved.replace(placeholder, str(val))
            
            # Direct comparisons
            if "==" in resolved:
                left, right = resolved.split("==")
                return left.strip().strip("'\"") == right.strip().strip("'\"")
            elif "!=" in resolved:
                left, right = resolved.split("!=")
                return left.strip().strip("'\"") != right.strip().strip("'\"")
            
            return bool(resolved)
        except Exception:
            return False

    @staticmethod
    async def execute_workflow(db: AsyncSession, execution: WorkflowExecution):
        """Runs the main DAG execution loop for a workflow execution instance."""
        if execution.status not in ["Running", "Draft"]:
            logger.info(f"WorkflowEngine: Execution '{execution.id}' is in status '{execution.status}'. Aborting run.")
            return

        if execution.status == "Draft":
            await WorkflowLifecycle.start_execution(db, execution)

        # 1. Fetch definition steps
        stmt = select(WorkflowDefinition).where(WorkflowDefinition.id == execution.workflow_id)
        res = await db.execute(stmt)
        wdef = res.scalar_one_or_none()

        if not wdef:
            await WorkflowLifecycle.fail_execution(db, execution, "Workflow definition not found.")
            return

        steps_list = wdef.definition.get("steps", [])
        steps_map = {step["name"]: step for step in steps_list if "name" in step}

        # Main Loop: Execute all ready nodes
        while True:
            # Load current step log history
            stmt_logs = select(WorkflowStepExecution).where(WorkflowStepExecution.execution_id == execution.id)
            res_logs = await db.execute(stmt_logs)
            step_logs = {log.step_name: log for log in res_logs.scalars().all()}

            completed_steps = {name for name, log in step_logs.items() if log.status == "Completed"}
            skipped_steps = {name for name, log in step_logs.items() if log.status == "Skipped"}
            failed_steps = {name for name, log in step_logs.items() if log.status == "Failed"}

            # If any step is Failed and exhausts recovery, the workflow is aborted and rolled back
            if failed_steps:
                logger.error(f"WorkflowEngine: Aborting execution {execution.id} due to failed steps: {failed_steps}")
                await WorkflowLifecycle.fail_execution(db, execution, f"Step failure: {failed_steps}")
                await WorkflowRollbackCoordinator.trigger_rollback(db, execution)
                return

            # Check if any step is currently Running/Waiting
            active_steps = {name for name, log in step_logs.items() if log.status in ["Running", "Waiting"]}
            if active_steps:
                # Execution is paused waiting for these async/human approval steps to resolve.
                # Update main workflow status to Waiting if a step is waiting on human approval
                if any(step_logs[name].status == "Waiting" for name in active_steps):
                    execution.status = "Waiting"
                    db.add(execution)
                    await db.flush()
                logger.info(f"WorkflowEngine: Execution '{execution.id}' is paused. Active steps: {active_steps}")
                return

            # Find all nodes that are ready to run
            ready_steps = []
            for step in steps_list:
                name = step["name"]
                if name in completed_steps or name in skipped_steps or name in failed_steps:
                    continue

                deps = step.get("dependencies", [])
                # All dependencies must be completed or skipped
                if all(dep in completed_steps or dep in skipped_steps for dep in deps):
                    ready_steps.append(step)

            # If no steps are ready
            if not ready_steps:
                # Check if all steps are completed or skipped
                all_done = all(step["name"] in completed_steps or step["name"] in skipped_steps for step in steps_list)
                if all_done:
                    await WorkflowLifecycle.complete_execution(db, execution)
                else:
                    # Deadlock check
                    logger.error(f"WorkflowEngine: Deadlock occurred in workflow execution {execution.id}.")
                    await WorkflowLifecycle.fail_execution(db, execution, "Deadlock occurred. Unable to schedule remaining steps.")
                return

            # Execute the ready steps sequentially in this batch to prevent DB session conflicts
            for step in ready_steps:
                await WorkflowEngine.run_step(db, execution, step)

            # Check if any step went to Waiting state. If so, return and let worker wait.
            # We must break loop to wait for external resume triggers.
            stmt_waiting = select(WorkflowStepExecution).where(
                WorkflowStepExecution.execution_id == execution.id,
                WorkflowStepExecution.status == "Waiting"
            )
            res_waiting = await db.execute(stmt_waiting)
            if res_waiting.scalars().first():
                execution.status = "Waiting"
                db.add(execution)
                await db.flush()
                return

    @staticmethod
    async def run_step(db: AsyncSession, execution: WorkflowExecution, step: Dict[str, Any]):
        """Runs a single workflow step with retry policies."""
        name = step["name"]
        
        # 1. Evaluate condition if specified
        condition = step.get("condition")
        if condition:
            # Flatten context values for condition check
            flat_ctx = {}
            for k, v in execution.context.items():
                if isinstance(v, dict) and "result" in v:
                    # e.g. step_1.result.status
                    for rk, rv in v["result"].items():
                        flat_ctx[f"{k}.result.{rk}"] = rv
                        flat_ctx[rk] = rv
                else:
                    flat_ctx[k] = v

            if not WorkflowEngine.evaluate_condition(condition, flat_ctx):
                logger.info(f"WorkflowEngine: Condition '{condition}' evaluated to False. Skipping step '{name}'")
                step_log = WorkflowStepExecution(
                    execution_id=execution.id,
                    step_name=name,
                    status="Skipped",
                    started_at=datetime.utcnow(),
                    completed_at=datetime.utcnow()
                )
                db.add(step_log)
                await db.flush()
                return

        # 2. Setup Step Log
        step_log = WorkflowStepExecution(
            execution_id=execution.id,
            step_name=name,
            status="Running",
            started_at=datetime.utcnow()
        )
        db.add(step_log)
        await db.flush()

        retry_policy = step.get("retry_policy", {})
        max_retries = retry_policy.get("max_retries", 1)
        backoff_ms = retry_policy.get("backoff_ms", 100)

        step_res = {}
        for attempt in range(max_retries):
            step_res = await WorkflowStepExecutor.execute_step(db, execution, step)
            status = step_res.get("status", "Completed")

            if status != "Failed":
                break
            if attempt < max_retries - 1:
                await asyncio.sleep(backoff_ms / 1000.0)

        # 3. Handle step results
        status = step_res.get("status", "Completed")
        step_log.status = status
        
        if status == "Completed":
            step_log.completed_at = datetime.utcnow()
            step_log.duration_ms = WorkflowMetrics.calculate_duration_ms(step_log.started_at, step_log.completed_at)
            
            # Save results into execution context
            context = dict(execution.context or {})
            context[name] = {"result": step_res.get("result", step_res)}
            # Also merge top level keys if result is dict
            if isinstance(step_res.get("result"), dict):
                for k, v in step_res["result"].items():
                    context[k] = v
            execution.context = context
            
            # Check step SLA limit breach
            sla_limit = step.get("sla_limit_seconds")
            if sla_limit:
                WorkflowMetrics.check_sla_breach(execution, sla_limit)

        elif status == "Waiting":
            # Human approval step registers wait status
            pass
        else:
            step_log.completed_at = datetime.utcnow()
            step_log.error = step_res.get("error", "Unknown Step Error")

        db.add(step_log)
        db.add(execution)
        await db.flush()
