import asyncio
import sys
import os

sys.path.insert(0, os.path.abspath("."))

from app.database.session import AsyncSessionLocal
from sqlalchemy import select
from app.models.conversations import Conversation

async def main():
    async with AsyncSessionLocal() as db:
        stmt = select(Conversation).where(Conversation.type.in_(["group", "project_channel", "announcement"]))
        res = await db.execute(stmt)
        groups = res.scalars().all()
        print(f"Total groups found in DB: {len(groups)}")
        for g in groups:
            print(f"- ID: {g.id} | Name: '{g.name}' | Type: {g.type} | CreatedAt: {g.created_at}")

if __name__ == "__main__":
    asyncio.run(main())
