from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from ...core.database import get_db_session
from ...models.user import User
from ...models.organization import Organization
from ...models.workspace import Workspace
from ...models.project import Project
from ...models.document import Document
from ...models.message import Message

router = APIRouter()

@router.get("/stats")
async def get_dashboard_stats(db: AsyncSession = Depends(get_db_session)):
    users_count = (await db.execute(select(func.count()).select_from(User))).scalar_one()
    orgs_count = (await db.execute(select(func.count()).select_from(Organization))).scalar_one()
    workspaces_count = (await db.execute(select(func.count()).select_from(Workspace))).scalar_one()
    projects_count = (await db.execute(select(func.count()).select_from(Project))).scalar_one()
    documents_count = (await db.execute(select(func.count()).select_from(Document))).scalar_one()
    messages_count = (await db.execute(select(func.count()).select_from(Message))).scalar_one()

    # Get recent projects
    projects_res = await db.execute(select(Project).limit(5))
    projects = projects_res.scalars().all()

    # Get recent documents
    docs_res = await db.execute(select(Document).limit(5))
    docs = docs_res.scalars().all()

    return {
        "stats": {
            "users": users_count,
            "organizations": orgs_count,
            "workspaces": workspaces_count,
            "projects": projects_count,
            "documents": documents_count,
            "messages": messages_count,
        },
        "recent_projects": [
            {"id": str(p.id), "name": p.name, "slug": p.slug} for p in projects
        ],
        "recent_documents": [
            {"id": str(d.id), "name": d.name, "mime_type": d.mime_type, "size": d.size} for d in docs
        ]
    }
