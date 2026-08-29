import sys, os
sys.path.insert(0, os.path.abspath("."))
import asyncio
from sqlalchemy import select
from app.core.database import AsyncSessionLocal
from app.documents.models import Document
from app.models.user import User

async def main():
    session = AsyncSessionLocal()
    res_user = await session.execute(select(User).where(User.email == 'testuser@mindmesh.com'))
    user = res_user.scalar_one_or_none()
    print('User org:', user.current_organization_id, 'ws:', user.current_workspace_id)
    
    res_docs = await session.execute(select(Document))
    docs = res_docs.scalars().all()
    print('Total documents in DB:', len(docs))
    for d in docs:
        print(f"Doc ID: {d.id} | Title: {d.title} | File Name: {getattr(d, 'file_name', getattr(d, 'filename', 'N/A'))} | Mime: {d.mime_type} | Ext: {getattr(d, 'file_extension', 'N/A')} | Deleted: {d.deleted_at} | Org: {d.organization_id} | WS: {d.workspace_id}")
        
    await session.close()

if __name__ == "__main__":
    asyncio.run(main())
