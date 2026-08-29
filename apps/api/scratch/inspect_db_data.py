import asyncio
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.core.database import AsyncSessionLocal
from sqlalchemy import text

async def inspect():
    async with AsyncSessionLocal() as session:
        u = (await session.execute(text("SELECT id, email, current_workspace_id FROM users WHERE email='testuser@mindmesh.com'"))).fetchone()
        print('User:', u)
        if u and u[2]:
            ws_id = str(u[2])
            tasks = (await session.execute(text("SELECT id, title, description, status FROM tasks WHERE workspace_id=:w"), {'w': ws_id})).fetchall()
            docs = (await session.execute(text("SELECT id, title, filename FROM documents WHERE workspace_id=:w"), {'w': ws_id})).fetchall()
            projs = (await session.execute(text("SELECT id, name FROM projects WHERE workspace_id=:w"), {'w': ws_id})).fetchall()
            mems = (await session.execute(text("SELECT id, content, memory_type FROM conversation_memories WHERE workspace_id=:w"), {'w': ws_id})).fetchall()
            print('Tasks:', len(tasks), tasks)
            print('Docs:', len(docs), docs)
            print('Projects:', len(projs), projs)
            print('Memories:', len(mems), mems)

if __name__ == '__main__':
    asyncio.run(inspect())
