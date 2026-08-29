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
from app.models.conversations import Conversation, DirectMessage
from app.models.audit import AuditLog
from app.models.graph import GraphNode, GraphEdge
from sqlalchemy import select

async def inspect_real_workspace_data():
    async with AsyncSessionLocal() as db:
        print("=== 1. ORGANIZATIONS & WORKSPACES ===")
        orgs = (await db.execute(select(Organization))).scalars().all()
        for o in orgs:
            print(f"Org: id={o.id}, name='{o.name}'")
        
        wss = (await db.execute(select(Workspace))).scalars().all()
        for w in wss:
            print(f"Workspace: id={w.id}, org_id={w.organization_id}, name='{w.name}'")

        print("\n=== 2. PROJECTS ===")
        projects = (await db.execute(select(Project))).scalars().all()
        for p in projects:
            print(f"Project: id={p.id}, name='{p.name}', status='{p.status}'")

        print("\n=== 3. TASKS ===")
        tasks = (await db.execute(select(Task))).scalars().all()
        for t in tasks:
            print(f"Task: id={t.id}, project_id={t.project_id}, status='{t.status}', title='{t.title or t.description[:40]}'")

        print("\n=== 4. DOCUMENTS ===")
        docs = (await db.execute(select(Document))).scalars().all()
        for d in docs:
            print(f"Document: id={d.id}, project_id={d.project_id}, title='{d.title}', filename='{d.filename}'")

        print("\n=== 5. CONVERSATION MEMORIES (DECISIONS / ACTION ITEMS) ===")
        mems = (await db.execute(select(ConversationMemory))).scalars().all()
        for m in mems:
            print(f"Memory: id={m.id}, type='{m.memory_type}', content='{m.content[:50]}'")

        print("\n=== 6. GRAPH NODES & EDGES ===")
        gnodes = (await db.execute(select(GraphNode))).scalars().all()
        print(f"Total Graph Nodes: {len(gnodes)}")
        for gn in gnodes[:10]:
            print(f"Node: id={gn.id}, type='{gn.node_type}', title='{gn.title}'")

        gedges = (await db.execute(select(GraphEdge))).scalars().all()
        print(f"Total Graph Edges: {len(gedges)}")
        for ge in gedges[:10]:
            print(f"Edge: id={ge.id}, src={ge.source_node_id}, tgt={ge.target_node_id}, rel='{ge.relation_type}', evidence='{ge.evidence_type}'")

if __name__ == "__main__":
    asyncio.run(inspect_real_workspace_data())
