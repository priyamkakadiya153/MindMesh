import sys, os
sys.path.insert(0, os.path.abspath("."))
import asyncio
from sqlalchemy import select, func, or_
from app.core.database import AsyncSessionLocal
from app.documents.models import Document
from app.models.user import User

async def main():
    session = AsyncSessionLocal()
    res_user = await session.execute(select(User).where(User.email == 'testuser@mindmesh.com'))
    user = res_user.scalar_one_or_none()
    print('User org:', user.current_organization_id, 'ws:', user.current_workspace_id)
    
    stmt = select(func.count(Document.id)).where(
        Document.organization_id == user.current_organization_id,
        Document.workspace_id == user.current_workspace_id,
        Document.deleted_at == None,
        or_(
            Document.extension.ilike('%pdf%'),
            Document.mime_type.ilike('%pdf%'),
            Document.filename.ilike('%pdf%'),
            Document.title.ilike('%pdf%')
        )
    )
    res = await session.execute(stmt)
    count = res.scalar() or 0
    print('DB PDF count:', count)
    await session.close()

if __name__ == "__main__":
    asyncio.run(main())
