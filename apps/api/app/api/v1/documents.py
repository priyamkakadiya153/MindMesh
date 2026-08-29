from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from ...core.database import get_db_session
from ...models.document import Document
from ...models.project import Project
from pydantic import BaseModel

router = APIRouter()

class DocumentCreate(BaseModel):
    name: str
    mime_type: str
    size: int
    storage_path: str

@router.get("/")
async def list_documents(db: AsyncSession = Depends(get_db_session)):
    res = await db.execute(select(Document))
    docs = res.scalars().all()
    return [{"id": str(d.id), "name": d.name, "mime_type": d.mime_type, "size": d.size, "storage_path": d.storage_path} for d in docs]

@router.post("/")
async def create_document(doc_in: DocumentCreate, db: AsyncSession = Depends(get_db_session)):
    project_res = await db.execute(select(Project).limit(1))
    project = project_res.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=400, detail="No active project found")

    new_doc = Document(
        name=doc_in.name,
        mime_type=doc_in.mime_type,
        size=doc_in.size,
        storage_path=doc_in.storage_path,
        project_id=project.id,
        organization_id=project.organization_id
    )
    db.add(new_doc)
    await db.flush()
    return {"id": str(new_doc.id), "name": new_doc.name, "mime_type": new_doc.mime_type, "size": new_doc.size}
