from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from ...core.database import get_db_session
from ...models.project import Project
from ...models.workspace import Workspace
from pydantic import BaseModel

router = APIRouter()

class ProjectCreate(BaseModel):
    name: str
    slug: str

@router.get("/")
async def list_projects(db: AsyncSession = Depends(get_db_session)):
    res = await db.execute(select(Project))
    projects = res.scalars().all()
    return [{"id": str(p.id), "name": p.name, "slug": p.slug} for p in projects]

@router.post("/")
async def create_project(project_in: ProjectCreate, db: AsyncSession = Depends(get_db_session)):
    workspace_res = await db.execute(select(Workspace).limit(1))
    workspace = workspace_res.scalar_one_or_none()
    if not workspace:
        raise HTTPException(status_code=400, detail="No active workspace found")

    new_project = Project(
        name=project_in.name,
        slug=project_in.slug,
        workspace_id=workspace.id,
        organization_id=workspace.organization_id
    )
    db.add(new_project)
    await db.flush()
    return {"id": str(new_project.id), "name": new_project.name, "slug": new_project.slug}
