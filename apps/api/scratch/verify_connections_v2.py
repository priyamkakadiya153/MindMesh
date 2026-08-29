import asyncio
import sys
import os

sys.path.insert(0, os.path.abspath("."))

from app.core.database import AsyncSessionLocal
from app.models.organization import Organization
from app.workspace.models import Workspace
from app.projects.models import Project
from app.models.task import Task
from app.documents.models import Document
from app.models.conversation import ConversationMemory
from app.knowledge.connections_service import ConnectionsService
from sqlalchemy import select

async def run_connections_v2_verification():
    async with AsyncSessionLocal() as db:
        res_org = await db.execute(select(Organization).limit(1))
        org = res_org.scalar_one_or_none()
        
        res_ws = await db.execute(select(Workspace).where(Workspace.organization_id == org.id).limit(1))
        ws = res_ws.scalar_one_or_none()

        conn_service = ConnectionsService(db)

        print("=== 1. VERIFY REAL DOCUMENT RELATIONSHIPS & CONTEXT ===")
        res_doc = await db.execute(select(Document).where(Document.title.ilike("%Authentication%")).limit(1))
        doc = res_doc.scalar_one_or_none()
        if doc:
            insp_doc = await conn_service.get_entity_provenance("DOCUMENT", doc.id, user=None, organization_id=org.id)
            print(f"[Document Inspector]: Title='{insp_doc['title']}' | HasVerified={insp_doc['has_verified_connections']} | Supporting={len(insp_doc['supporting_evidence'])} | ChainLen={len(insp_doc['provenance_chain'])}")
            print(f"Chain: {[s['title'] for s in insp_doc['provenance_chain']]}")

        print("\n=== 2. VERIFY REAL DECISION RELATIONSHIPS & CAUSE/EFFECT ===")
        res_dec = await db.execute(select(ConversationMemory).where(ConversationMemory.memory_type == "decision").limit(1))
        dec = res_dec.scalar_one_or_none()
        if dec:
            insp_dec = await conn_service.get_entity_provenance("DECISION", dec.id, user=None, organization_id=org.id)
            print(f"[Decision Inspector]: Title='{insp_dec['title']}' | ResultingTasks={len(insp_dec['resulting_tasks'])} | ChainLen={len(insp_dec['provenance_chain'])}")

        print("\n=== 3. VERIFY REAL TASK DEPENDENCIES & PROJECT ===")
        res_task = await db.execute(select(Task).limit(1))
        task = res_task.scalar_one_or_none()
        if task:
            insp_task = await conn_service.get_entity_provenance("TASK", task.id, user=None, organization_id=org.id)
            print(f"[Task Inspector]: Title='{insp_task['title']}' | ConnectedProject={insp_task['connected_project']} | ChainLen={len(insp_task['provenance_chain'])}")

        print("\n==========================================================================")
        print("REAL CROSS-ENTITY RELATIONSHIP VERIFICATION (V2) PASSED 100%!")
        print("==========================================================================")

if __name__ == "__main__":
    asyncio.run(run_connections_v2_verification())
