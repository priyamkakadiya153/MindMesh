import asyncio
import sys
import os

sys.path.insert(0, os.path.abspath("."))

from app.database.session import AsyncSessionLocal
from sqlalchemy import select, delete
from app.models.conversations import Conversation, ConversationMember, DirectMessage

async def cleanup_duplicates():
    print("==================================================")
    print("  DEDUPLICATING GROUPS IN POSTGRESQL")
    print("==================================================")

    async with AsyncSessionLocal() as db:
        stmt = select(Conversation).where(Conversation.type.in_(["group", "project_channel", "announcement"])).order_by(Conversation.created_at.asc())
        res = await db.execute(stmt)
        groups = res.scalars().all()

        seen_names = set()
        to_delete_ids = []

        for g in groups:
            name_key = (g.name or "").strip().lower()
            if name_key in seen_names or name_key == "discuss":
                to_delete_ids.append(g.id)
            else:
                seen_names.add(name_key)

        print(f"Identified {len(to_delete_ids)} duplicate/obsolete groups for deletion.")

        if to_delete_ids:
            # Delete messages
            await db.execute(delete(DirectMessage).where(DirectMessage.conversation_id.in_(to_delete_ids)))
            # Delete members
            await db.execute(delete(ConversationMember).where(ConversationMember.conversation_id.in_(to_delete_ids)))
            # Delete groups
            await db.execute(delete(Conversation).where(Conversation.id.in_(to_delete_ids)))
            await db.commit()
            print(f"[SUCCESS] Purged {len(to_delete_ids)} duplicate groups.")

if __name__ == "__main__":
    asyncio.run(cleanup_duplicates())
