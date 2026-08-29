import logging
from typing import Dict, Callable, List, Any, Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from app.agents.context import SessionContext
from app.agents.tools.metadata import ToolMetadata
from app.search.service import SearchService
from app.projects.service import ProjectService
from app.notifications.service import NotificationService
from app.models.task import Task
from datetime import datetime

logger = logging.getLogger(__name__)

class ToolRegistry:
    def __init__(self):
        self._tools: Dict[str, Callable] = {}
        self._metadata: Dict[str, ToolMetadata] = {}

    def register(self, name: str, func: Callable, metadata: ToolMetadata):
        """Registers a tool function with its metadata."""
        self._tools[name] = func
        self._metadata[name] = metadata
        logger.info(f"Registered tool '{name}' version {metadata.version}")

    def get_tool(self, name: str) -> Optional[Callable]:
        """Retrieves the executable tool function."""
        return self._tools.get(name)

    def get_metadata(self, name: str) -> Optional[ToolMetadata]:
        """Retrieves tool metadata."""
        return self._metadata.get(name)

    def list_tools(self) -> List[ToolMetadata]:
        """Lists all registered tools."""
        return list(self._metadata.values())

    def clear(self):
        """Clears all tools in the registry."""
        self._tools.clear()
        self._metadata.clear()

# Global registry instance
tool_registry = ToolRegistry()

# Define built-in tool implementations

async def search_documents_tool(context: SessionContext, db: AsyncSession, query: str, limit: int = 5) -> Dict[str, Any]:
    """Search enterprise documents using hybrid semantic search."""
    search_service = SearchService(db)
    filters = {}
    if context.workspace_id:
        filters["workspace_id"] = str(context.workspace_id)
    if context.project_id:
        filters["project_id"] = str(context.project_id)

    res = await search_service.execute_hybrid_search(
        org_id=context.organization_id,
        query=query,
        limit=limit,
        filters=filters,
        user_id=context.user_id,
        workspace_id=context.workspace_id
    )
    return res

async def create_task_tool(
    context: SessionContext,
    db: AsyncSession,
    description: str,
    project_id: Optional[str] = None,
    due_date: Optional[str] = None
) -> Dict[str, Any]:
    """Create a task for a project within the workspace."""
    proj_id = UUID(project_id) if project_id else context.project_id
    parsed_due = datetime.fromisoformat(due_date) if due_date else None

    task = Task(
        description=description,
        status="PENDING",
        due_date=parsed_due,
        organization_id=context.organization_id,
        project_id=proj_id
    )
    db.add(task)
    await db.commit()
    await db.refresh(task)

    return {
        "id": str(task.id),
        "description": task.description,
        "status": task.status,
        "due_date": task.due_date.isoformat() if task.due_date else None,
        "project_id": str(task.project_id) if task.project_id else None
    }

async def send_notification_tool(
    context: SessionContext,
    db: AsyncSession,
    recipient_id: str,
    message: str,
    title: str = "Agent Notification"
) -> Dict[str, Any]:
    """Send a notification to a specific user."""
    notif_service = NotificationService(db)
    notif = await notif_service.create_notification(
        user_id=UUID(recipient_id),
        title=title,
        message=message,
        type="info",
        priority="normal"
    )
    return {
        "id": str(notif.id),
        "recipient_id": recipient_id,
        "title": title,
        "message": message,
        "created_at": notif.created_at.isoformat() if notif.created_at else None
    }

async def create_project_tool(
    context: SessionContext,
    db: AsyncSession,
    name: str,
    workspace_id: Optional[str] = None,
    description: Optional[str] = None,
    icon: Optional[str] = None,
    color: Optional[str] = None
) -> Dict[str, Any]:
    """Create a new project in the workspace."""
    ws_id = UUID(workspace_id) if workspace_id else context.workspace_id
    if not ws_id:
        raise ValueError("workspace_id must be provided or present in context.")

    project_service = ProjectService(db)
    project = await project_service.create_project(
        name=name,
        workspace_id=ws_id,
        org_id=context.organization_id,
        user_id=context.user_id,
        description=description,
        icon=icon,
        color=color,
        visibility="private"
    )
    return {
        "id": str(project.id),
        "name": project.name,
        "slug": project.slug,
        "workspace_id": str(project.workspace_id),
        "organization_id": str(project.organization_id),
        "owner_id": str(project.owner_id)
    }

def register_built_in_tools():
    """Helper to register all standard platform tools."""
    tool_registry.register(
        name="search_documents",
        func=search_documents_tool,
        metadata=ToolMetadata(
            name="search_documents",
            description="Search enterprise documents using hybrid semantic search.",
            version="1.0.0",
            permissions=["documents.read"],
            input_schema={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "The search keywords or natural query"},
                    "limit": {"type": "integer", "description": "Maximum results to return"}
                },
                "required": ["query"]
            }
        )
    )

    tool_registry.register(
        name="create_task",
        func=create_task_tool,
        metadata=ToolMetadata(
            name="create_task",
            description="Create a task for a project within the workspace.",
            version="1.0.0",
            permissions=["tasks.write"],
            input_schema={
                "type": "object",
                "properties": {
                    "description": {"type": "string", "description": "Details of the task to create"},
                    "project_id": {"type": "string", "description": "UUID string of the project"},
                    "due_date": {"type": "string", "description": "ISO format date string"}
                },
                "required": ["description"]
            }
        )
    )

    tool_registry.register(
        name="send_notification",
        func=send_notification_tool,
        metadata=ToolMetadata(
            name="send_notification",
            description="Send a system notification to a specific user.",
            version="1.0.0",
            permissions=["notifications.write"],
            input_schema={
                "type": "object",
                "properties": {
                    "recipient_id": {"type": "string", "description": "UUID string of the recipient user"},
                    "message": {"type": "string", "description": "Message body to send"},
                    "title": {"type": "string", "description": "Notification title"}
                },
                "required": ["recipient_id", "message"]
            }
        )
    )

    tool_registry.register(
        name="create_project",
        func=create_project_tool,
        metadata=ToolMetadata(
            name="create_project",
            description="Create a new project in the workspace.",
            version="1.0.0",
            permissions=["projects.write"],
            input_schema={
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "Name of the project"},
                    "workspace_id": {"type": "string", "description": "Workspace ID under which to create project"},
                    "description": {"type": "string", "description": "Project description"},
                    "icon": {"type": "string", "description": "Project icon class name"},
                    "color": {"type": "string", "description": "Hex color code"}
                },
                "required": ["name"]
            }
        )
    )
