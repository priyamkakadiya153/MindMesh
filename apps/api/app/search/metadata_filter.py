import logging
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from ..workspace.models import Workspace
from ..projects.models import Project

logger = logging.getLogger(__name__)

async def resolve_filter_ids(db: AsyncSession, org_id: UUID, filters: dict) -> dict:
    """Translates user-facing slug/name filters (like workspace, project) into UUIDs."""
    resolved = {}
    
    # 1. Resolve workspace slug/name to workspace_id
    if "workspace" in filters:
        ws_val = filters["workspace"]
        stmt = select(Workspace.id).where(
            Workspace.organization_id == org_id,
            (Workspace.slug == ws_val) | (Workspace.name == ws_val),
            Workspace.is_active == True
        )
        ws_id = (await db.execute(stmt)).scalar()
        if ws_id:
            resolved["workspace_id"] = str(ws_id)
        else:
            logger.warning(f"Failed to resolve workspace filter slug: '{ws_val}'")
            resolved["workspace_id"] = str(UUID(int=0)) # secure fallback returns nothing

    # 2. Resolve project slug/name to project_id
    if "project" in filters:
        proj_val = filters["project"]
        stmt = select(Project.id).where(
            Project.organization_id == org_id,
            (Project.slug == proj_val) | (Project.name == proj_val),
            Project.is_active == True
        )
        proj_id = (await db.execute(stmt)).scalar()
        if proj_id:
            resolved["project_id"] = str(proj_id)
        else:
            logger.warning(f"Failed to resolve project filter slug: '{proj_val}'")
            resolved["project_id"] = str(UUID(int=0))

    # 3. Direct filters forwarding
    if "tag" in filters:
        resolved["tag"] = filters["tag"]
    if "author" in filters:
        resolved["author"] = filters["author"]
    if "file_type" in filters:
        resolved["file_type"] = filters["file_type"]
    if "created_after" in filters:
        resolved["created_after"] = filters["created_after"]
        
    return resolved
