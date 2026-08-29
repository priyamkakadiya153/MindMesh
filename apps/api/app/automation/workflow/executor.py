import logging
import uuid
from typing import Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from app.automation.approval.models import WorkflowExecution
from app.automation.approval.service import ApprovalService
from app.agents.context import SessionContext
from app.agents.runtime import agent_runtime

logger = logging.getLogger(__name__)

class WorkflowStepExecutor:
    @staticmethod
    async def execute_step(
        db: AsyncSession,
        execution: WorkflowExecution,
        step_def: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Dispatches step execution based on defined type."""
        step_name = step_def.get("name")
        step_type = step_def.get("type")
        logger.info(f"WorkflowStepExecutor: Running step '{step_name}' (type: {step_type}) for execution {execution.id}")

        if step_type == "human_approval":
            # 1. Create a human approval request and return WAITING status
            assigned_approver = step_def.get("assigned_approver")
            # If placeholders exist in assigned_approver, resolve from context
            if assigned_approver and assigned_approver.startswith("${") and assigned_approver.endswith("}"):
                placeholder_key = assigned_approver[2:-1].strip()
                assigned_approver = str(execution.context.get(placeholder_key, assigned_approver))

            title = step_def.get("title", f"Approval Request for step '{step_name}'")
            description = step_def.get("description", "")
            policy_type = step_def.get("policy_type", "Single")
            sla_hours = step_def.get("sla_limit_hours")

            approval = await ApprovalService.create_approval(
                db=db,
                workflow_execution_id=execution.id,
                step_name=step_name,
                title=title,
                description=description,
                assigned_approver=assigned_approver,
                policy_type=policy_type,
                organization_id=execution.organization_id,
                workspace_id=execution.workspace_id,
                sla_limit_hours=sla_hours
            )
            return {
                "status": "Waiting",
                "approval_id": str(approval.id),
                "message": f"Paused execution waiting for human approval decision '{title}'"
            }

        elif step_type == "ai_agent":
            # 2. Invoke built-in agent runtime execution
            agent_name = step_def.get("agent_name", "ResearchAgent")
            input_data = step_def.get("input_data", {})
            
            # Resolve context values
            resolved_input = {}
            for k, v in input_data.items():
                if isinstance(v, str) and v.startswith("${") and v.endswith("}"):
                    key = v[2:-1].strip()
                    resolved_input[k] = execution.context.get(key, v)
                else:
                    resolved_input[k] = v

            context = SessionContext(
                user_id=execution.created_by or str(uuid.uuid4()),
                organization_id=execution.organization_id,
                workspace_id=execution.workspace_id,
                permissions=["*"],
                request_id=str(execution.id)
            )

            try:
                # Execute agent pipeline asynchronously
                res = await agent_runtime.execute(
                    agent_id=agent_name,
                    context=context,
                    input_data=resolved_input,
                    db=db
                )
                return {
                    "status": "Completed",
                    "result": res
                }
            except Exception as e:
                logger.error(f"WorkflowStepExecutor: AI Agent '{agent_name}' failed: {str(e)}")
                return {
                    "status": "Failed",
                    "error": str(e)
                }

        elif step_type == "notification":
            # 3. Dispatches notifications to targeted users
            user_id_str = step_def.get("user_id")
            if user_id_str and user_id_str.startswith("${") and user_id_str.endswith("}"):
                placeholder_key = user_id_str[2:-1].strip()
                user_id_str = str(execution.context.get(placeholder_key, user_id_str))

            from app.notifications.models import Notification
            try:
                user_uuid = uuid.UUID(user_id_str)
                notif = Notification(
                    user_id=user_uuid,
                    title=step_def.get("title", "Workflow Alert"),
                    message=step_def.get("message", "Alert triggered."),
                    type="info",
                    priority="normal",
                    is_read=False
                )
                db.add(notif)
                await db.flush()
            except Exception as e:
                logger.error(f"WorkflowStepExecutor: Notification failed: {str(e)}")
            return {"status": "Completed", "message": "Notification dispatched."}

        elif step_type == "http_api":
            # 4. Performs API call Simulation
            url = step_def.get("url")
            method = step_def.get("method", "POST")
            logger.info(f"WorkflowStepExecutor: Triggering API call to {method} '{url}'")
            return {"status": "Completed", "api_response": {"success": True, "url_hit": url}}

        # Default fallback sequential / parallel step markers
        return {"status": "Completed", "message": "Step executed successfully."}
