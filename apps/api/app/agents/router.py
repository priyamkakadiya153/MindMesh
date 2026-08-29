import logging
import uuid
from typing import Dict, Any, List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db_session
from app.api.dependencies import get_current_user
from app.authorization.organization_resolver import resolve_organization_id
from app.models.user import User
from app.models.agent import Agent as DBAgent

from app.agents.context import SessionContext
from app.agents.runtime import agent_runtime
from app.agents.tools.registry import tool_registry
from app.agents.exceptions import PermissionDeniedException, AgentNotFoundException
from app.agents.metrics import metrics_tracker

logger = logging.getLogger(__name__)

router = APIRouter()

# ----------------- AGENT ENDPOINTS -----------------

@router.get("/agents", response_model=List[Dict[str, Any]], status_code=status.HTTP_200_OK)
async def list_agents(
    current_user: User = Depends(get_current_user),
    org_id: str = Depends(resolve_organization_id),
    db: AsyncSession = Depends(get_db_session)
):
    """Lists all code-based registered agents and database-defined agents for the organization."""
    from app.agents.registry import agent_registry
    
    # 1. Code-based agents
    reg_agents = agent_registry.list_agents()
    
    # 2. Database agents
    org_uuid = uuid.UUID(org_id) if isinstance(org_id, str) else org_id
    stmt = select(DBAgent).where(DBAgent.organization_id == org_uuid)
    res = await db.execute(stmt)
    db_agents = res.scalars().all()
    
    formatted_db_agents = [
        {
            "id": str(agent.id),
            "name": agent.name,
            "description": f"Generic DB Agent running as {agent.role}",
            "version": "1.0.0",
            "required_permissions": []
        }
        for agent in db_agents
    ]

    # Merge database agents with code-based agents based on name
    seen_names = {a["name"] for a in reg_agents}
    for db_a in formatted_db_agents:
        if db_a["name"] not in seen_names:
            reg_agents.append(db_a)

    return reg_agents

@router.get("/agents/{id}", response_model=Dict[str, Any], status_code=status.HTTP_200_OK)
async def get_agent_details(
    id: str,
    current_user: User = Depends(get_current_user),
    org_id: str = Depends(resolve_organization_id),
    db: AsyncSession = Depends(get_db_session)
):
    """Retrieves full metadata/details of a specific agent by ID/name."""
    from app.agents.registry import agent_registry

    # Check code registry
    agent_cls = agent_registry.get_agent(id)
    if agent_cls:
        meta = getattr(agent_cls, "_agent_meta", {})
        return {
            "id": id,
            "name": meta.get("name", agent_cls.__name__),
            "description": meta.get("description", ""),
            "version": meta.get("version", "1.0.0"),
            "required_permissions": meta.get("required_permissions", [])
        }

    # Check database
    try:
        agent_uuid = uuid.UUID(id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agent '{id}' was not found in registry and is not a valid database UUID."
        )

    stmt = select(DBAgent).where(DBAgent.id == agent_uuid)
    res = await db.execute(stmt)
    db_agent = res.scalar_one_or_none()
    if not db_agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agent with database ID {id} not found."
        )

    return {
        "id": str(db_agent.id),
        "name": db_agent.name,
        "description": f"Generic DB Agent running as {db_agent.role}",
        "version": "1.0.0",
        "required_permissions": []
    }

@router.post("/agents/{id}/execute", response_model=Dict[str, Any], status_code=status.HTTP_200_OK)
async def execute_agent(
    id: str,
    payload: Dict[str, Any],
    current_user: User = Depends(get_current_user),
    org_id: str = Depends(resolve_organization_id),
    db: AsyncSession = Depends(get_db_session)
):
    """Executes a specific agent task with input arguments."""
    org_uuid = uuid.UUID(org_id) if isinstance(org_id, str) else org_id
    
    workspace_id = payload.get("workspace_id")
    project_id = payload.get("project_id")
    conversation_id = payload.get("conversation_id")
    input_data = payload.get("input", {})

    ws_uuid = uuid.UUID(workspace_id) if workspace_id else None
    proj_uuid = uuid.UUID(project_id) if project_id else None
    conv_uuid = uuid.UUID(conversation_id) if conversation_id else None

    request_id = str(uuid.uuid4())
    
    # Create Execution Context with default wildcard permissions for system operations
    context = SessionContext(
        user_id=current_user.id,
        organization_id=org_uuid,
        workspace_id=ws_uuid,
        project_id=proj_uuid,
        conversation_id=conv_uuid,
        permissions=["*"],  # Default wildcard permissions
        request_id=request_id
    )

    try:
        result = await agent_runtime.execute(
            agent_id=id,
            context=context,
            input_data=input_data,
            db=db
        )
        return result
    except PermissionDeniedException as pe:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(pe))
    except AgentNotFoundException as ae:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(ae))
    except Exception as e:
        logger.error(f"Agent execution endpoint failed: {str(e)}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.get("/agents/{id}/status", response_model=Dict[str, Any], status_code=status.HTTP_200_OK)
async def get_agent_status(
    id: str,
    current_user: User = Depends(get_current_user)
):
    """Retrieves operational status and execution metrics of a specific agent."""
    from app.agents.registry import agent_registry
    
    # Verify agent exists in registry or database structure (simple validation)
    agent_cls = agent_registry.get_agent(id)
    name_lookup = id
    if agent_cls:
        name_lookup = getattr(agent_cls, "_agent_meta", {}).get("name", agent_cls.__name__)

    stats = metrics_tracker.get_metrics_summary()
    agent_stats = stats["agents"].get(name_lookup)
    if not agent_stats:
        return {
            "id": id,
            "status": "idle",
            "executions": 0,
            "success_rate": 1.0,
            "avg_latency_ms": 0.0
        }
    return {
        "id": id,
        "status": "idle",
        **agent_stats
    }

# ----------------- TOOL ENDPOINTS -----------------

@router.get("/tools", response_model=List[Dict[str, Any]], status_code=status.HTTP_200_OK)
async def list_tools(
    current_user: User = Depends(get_current_user)
):
    """Lists all available enterprise tools and their schemas."""
    tools = tool_registry.list_tools()
    return [t.model_dump() for t in tools]

@router.get("/tools/discover", response_model=List[Dict[str, Any]], status_code=status.HTTP_200_OK)
async def discover_tools(
    current_user: User = Depends(get_current_user)
):
    """Redirects to standard tools list to discover tools."""
    tools = tool_registry.list_tools()
    return [t.model_dump() for t in tools]

@router.get("/tools/{name}", response_model=Dict[str, Any], status_code=status.HTTP_200_OK)
async def get_tool_details(
    name: str,
    current_user: User = Depends(get_current_user)
):
    """Retrieves detailed schemas for a specific tool."""
    metadata = tool_registry.get_metadata(name)
    if not metadata:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tool '{name}' was not found in registry."
        )
    return metadata.model_dump()

# ----------------- COGNITIVE PLANNING & ORCHESTRATED EXECUTION ENDPOINTS -----------------
# Simple memory caches for execution history
plans_cache: Dict[str, Dict[str, Any]] = {}
executions_cache: Dict[str, Dict[str, Any]] = {}

@router.post("/agents/plan", response_model=Dict[str, Any], status_code=status.HTTP_200_OK)
async def generate_plan(
    payload: Dict[str, Any],
    current_user: User = Depends(get_current_user),
    org_id: str = Depends(resolve_organization_id)
):
    """Generates an execution plan for a goal and runs Decision Engine analysis."""
    from app.agents.planning.planner import PlanningEngine
    from app.agents.reasoning.decision import DecisionEngine

    goal = payload.get("goal")
    if not goal:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Missing required field: 'goal'")

    use_llm = payload.get("use_llm", True)

    try:
        graph = await PlanningEngine.create_plan(goal, use_llm=use_llm)
        feasibility = DecisionEngine.evaluate_plan_feasibility(graph)
        
        plan_id = str(uuid.uuid4())
        plan_data = {
            "plan_id": plan_id,
            "goal": goal,
            "feasibility": feasibility,
            "graph": graph.serialize()
        }
        plans_cache[plan_id] = plan_data
        return plan_data
    except Exception as e:
        logger.error(f"Plan generation failed: {str(e)}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.get("/agents/plan/{plan_id}", response_model=Dict[str, Any], status_code=status.HTTP_200_OK)
async def get_plan_details(
    plan_id: str,
    current_user: User = Depends(get_current_user)
):
    """Fetches plan details from plan cache."""
    plan = plans_cache.get(plan_id)
    if not plan:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Plan '{plan_id}' not found.")
    return plan

@router.post("/agents/execute", response_model=Dict[str, Any], status_code=status.HTTP_200_OK)
async def execute_goal(
    payload: Dict[str, Any],
    current_user: User = Depends(get_current_user),
    org_id: str = Depends(resolve_organization_id),
    db: AsyncSession = Depends(get_db_session)
):
    """Generates a plan for the goal and executes it through the DAG orchestrator."""
    from app.agents.planning.planner import PlanningEngine
    from app.agents.execution.orchestrator import GraphOrchestrator
    from app.agents.reasoning.evaluator import FinalEvaluator

    goal = payload.get("goal")
    if not goal:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Missing required field: 'goal'")

    use_llm = payload.get("use_llm", True)
    
    # Context setup
    workspace_id = payload.get("workspace_id")
    project_id = payload.get("project_id")
    conversation_id = payload.get("conversation_id")

    ws_uuid = uuid.UUID(workspace_id) if workspace_id else None
    proj_uuid = uuid.UUID(project_id) if project_id else None
    conv_uuid = uuid.UUID(conversation_id) if conversation_id else None
    org_uuid = uuid.UUID(org_id) if isinstance(org_id, str) else org_id
    
    request_id = str(uuid.uuid4())
    context = SessionContext(
        user_id=current_user.id,
        organization_id=org_uuid,
        workspace_id=ws_uuid,
        project_id=proj_uuid,
        conversation_id=conv_uuid,
        permissions=["*"],
        request_id=request_id
    )

    try:
        # 1. Create plan
        graph = await PlanningEngine.create_plan(goal, use_llm=use_llm)
        
        # 2. Run orchestrator
        orchestrator = GraphOrchestrator(graph)
        results = await orchestrator.execute(context, db)
        
        # 3. Evaluate results
        evaluation = FinalEvaluator.evaluate_execution(graph)
        
        execution_id = request_id
        exec_data = {
            "execution_id": execution_id,
            "goal": goal,
            "evaluation": evaluation,
            "results": results
        }
        executions_cache[execution_id] = exec_data
        return exec_data
    except Exception as e:
        logger.error(f"Goal execution failed: {str(e)}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.get("/agents/executions/{execution_id}", response_model=Dict[str, Any], status_code=status.HTTP_200_OK)
async def get_execution_status(
    execution_id: str,
    current_user: User = Depends(get_current_user)
):
    """Fetches execution session status and results."""
    exec_data = executions_cache.get(execution_id)
    if not exec_data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Execution '{execution_id}' not found.")
    return exec_data

@router.post("/tools/execute", response_model=Dict[str, Any], status_code=status.HTTP_200_OK)
async def execute_tool_directly(
    payload: Dict[str, Any],
    current_user: User = Depends(get_current_user),
    org_id: str = Depends(resolve_organization_id),
    db: AsyncSession = Depends(get_db_session)
):
    """Executes a single tool call directly through the tool pipeline."""
    from app.agents.execution.pipeline import ToolCallPipeline

    tool_name = payload.get("name")
    input_data = payload.get("input", {})
    if not tool_name:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Missing required field: 'name'")

    workspace_id = payload.get("workspace_id")
    project_id = payload.get("project_id")
    conversation_id = payload.get("conversation_id")

    ws_uuid = uuid.UUID(workspace_id) if workspace_id else None
    proj_uuid = uuid.UUID(project_id) if project_id else None
    conv_uuid = uuid.UUID(conversation_id) if conversation_id else None
    org_uuid = uuid.UUID(org_id) if isinstance(org_id, str) else org_id

    context = SessionContext(
        user_id=current_user.id,
        organization_id=org_uuid,
        workspace_id=ws_uuid,
        project_id=proj_uuid,
        conversation_id=conv_uuid,
        permissions=["*"],
        request_id=str(uuid.uuid4())
    )

    result = await ToolCallPipeline.run_single_tool(
        tool_name=tool_name,
        input_data=input_data,
        context=context,
        db=db
    )
    return result


@router.post("/agents/reflect", response_model=Dict[str, Any], status_code=status.HTTP_200_OK)
async def force_reflection(
    payload: Dict[str, Any],
    current_user: User = Depends(get_current_user)
):
    """Forces reflection evaluation of custom inputs/outputs."""
    from app.agents.reasoning.reflection import ReflectionEngine

    tool_name = payload.get("tool")
    result = payload.get("result")
    error = payload.get("error")

    if not tool_name:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Missing required field: 'tool'")

    evaluation = ReflectionEngine.evaluate(tool_name, result, error)
    return evaluation

# ----------------- ENTERPRISE MULTI-AGENT ORCHESTRATION ENDPOINTS -----------------
orchestrator_executions: Dict[str, Dict[str, Any]] = {}

@router.post("/orchestrator/execute", response_model=Dict[str, Any], status_code=status.HTTP_200_OK)
async def execute_orchestrator(
    payload: Dict[str, Any],
    current_user: User = Depends(get_current_user),
    org_id: str = Depends(resolve_organization_id),
    db: AsyncSession = Depends(get_db_session)
):
    """Executes a multi-agent team workflow coordinator on a goal."""
    from app.agents.orchestrator.supervisor import SupervisorAgent

    goal = payload.get("goal")
    if not goal:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Missing required field: 'goal'")

    workspace_id = payload.get("workspace_id")
    project_id = payload.get("project_id")
    conversation_id = payload.get("conversation_id")

    ws_uuid = uuid.UUID(workspace_id) if workspace_id else None
    proj_uuid = uuid.UUID(project_id) if project_id else None
    conv_uuid = uuid.UUID(conversation_id) if conversation_id else None
    org_uuid = uuid.UUID(org_id) if isinstance(org_id, str) else org_id

    request_id = str(uuid.uuid4())
    context = SessionContext(
        user_id=current_user.id,
        organization_id=org_uuid,
        workspace_id=ws_uuid,
        project_id=proj_uuid,
        conversation_id=conv_uuid,
        permissions=["*"],
        request_id=request_id
    )

    try:
        supervisor = SupervisorAgent()
        res = await supervisor.run_workflow(goal, context, db)
        orchestrator_executions[request_id] = res
        return res
    except Exception as e:
        logger.error(f"Orchestrator workflow failed: {str(e)}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.get("/orchestrator/{executionId}", response_model=Dict[str, Any], status_code=status.HTTP_200_OK)
async def get_orchestrator_execution(
    executionId: str,
    current_user: User = Depends(get_current_user)
):
    """Retrieves operational details of a specific orchestrator run."""
    exec_data = orchestrator_executions.get(executionId)
    if not exec_data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Execution '{executionId}' not found.")
    return exec_data

@router.post("/agents/delegate", response_model=Dict[str, Any], status_code=status.HTTP_200_OK)
async def delegate_agent_task(
    payload: Dict[str, Any],
    current_user: User = Depends(get_current_user)
):
    """Matches a task description to the most appropriate specialized agent class name."""
    from app.agents.collaboration.delegation import DelegationEngine

    description = payload.get("description")
    if not description:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Missing required field: 'description'")

    agent_name = DelegationEngine.delegate_task(description)
    return {"task_description": description, "assigned_agent": agent_name}

@router.post("/agents/message", response_model=Dict[str, Any], status_code=status.HTTP_200_OK)
async def send_agent_message(
    payload: Dict[str, Any],
    current_user: User = Depends(get_current_user)
):
    """Sends a message payload to target agents via the central MessageBus."""
    from app.agents.communication.protocol import AgentMessage
    from app.agents.communication.routing import MessageRouter

    sender = payload.get("sender")
    receiver = payload.get("receiver")
    msg_payload = payload.get("payload", {})
    conversation_id = payload.get("conversation_id")

    if not sender or not receiver:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Missing required fields: 'sender' and 'receiver'")

    msg = AgentMessage(
        sender=sender,
        receiver=receiver,
        conversation_id=conversation_id,
        payload=msg_payload
    )

    await MessageRouter.route_message(msg)
    return {"status": "SENT", "message": msg.model_dump()}

@router.get("/executions", response_model=List[Dict[str, Any]], status_code=status.HTTP_200_OK)
async def list_agent_team_executions(
    current_user: User = Depends(get_current_user)
):
    """Lists all registered agent team execution sessions."""
    return list(orchestrator_executions.values())

@router.get("/executions/{id}", response_model=Dict[str, Any], status_code=status.HTTP_200_OK)
async def get_agent_team_execution_details(
    id: str,
    current_user: User = Depends(get_current_user)
):
    """Retrieves operational details of a specific execution session."""
    exec_data = orchestrator_executions.get(id)
    if not exec_data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Execution '{id}' not found.")
    return exec_data
