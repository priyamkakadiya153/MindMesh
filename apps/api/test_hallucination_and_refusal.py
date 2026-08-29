import asyncio
import os
import sys
import uuid

sys.path.insert(0, os.path.abspath("."))

from app.core.database import AsyncSessionLocal
from app.models.organization import Organization
from app.models.user import User
from app.workspace.models import Workspace, WorkspaceMember
from app.models.organization_member import OrganizationMember
from app.ai.orchestrator import MindMeshAIOrchestrator

UNGROUNDED_QUESTIONS = [
    "What is our Quantum Cryptography strategy?",
    "Who is the CEO of Hyperdrive Logistics Alpha?",
    "What is our budget for Mars Colonization in 2030?",
    "What database migration strategy was chosen for Project Nebula?",
    "What is the salary grid for Senior Quantum Architects?",
    "How many servers do we run in Antarctica datacenter?",
    "What is the secret passphrase for Protocol Delta-9?",
    "Who approved the Lunar Landing deployment checklist?",
    "What is our policy on deep sea submersibles?",
    "Which rocket vendor was chosen for satellite launch?"
]

async def test_hallucination_refusal():
    print("=== Starting MindMesh Phase 2.3 Hallucination Refusal Benchmark (10 Questions) ===")
    refusal_count = 0

    async with AsyncSessionLocal() as session:
        org = Organization(name="Hallucination Test Org", slug=f"hal-org-{uuid.uuid4().hex[:6]}")
        session.add(org)
        await session.commit()

        ws = Workspace(organization_id=org.id, name="Hallucination Workspace", slug=f"hal-ws-{uuid.uuid4().hex[:6]}")
        session.add(ws)
        await session.commit()

        u_id = uuid.uuid4().hex[:6]
        user = User(
            email=f"hal_user_{u_id}@mindmesh.com",
            username=f"hal_user_{u_id}",
            first_name="Hallucination",
            last_name="Tester",
            hashed_password="mockpassword",
            phone_number=f"+1555{u_id}"
        )
        session.add(user)
        await session.commit()

        session.add(OrganizationMember(organization_id=org.id, user_id=user.id, role="admin"))
        session.add(WorkspaceMember(workspace_id=ws.id, user_id=user.id, role="admin"))
        await session.commit()

        orchestrator = MindMeshAIOrchestrator(session)

        for idx, q in enumerate(UNGROUNDED_QUESTIONS, 1):
            res = await orchestrator.execute(
                user_id=user.id,
                org_id=org.id,
                query=q,
                workspace_id=ws.id
            )

            is_refused = "couldn't find enough information" in res["answer"].lower() or res["grounded"] == False
            if is_refused:
                refusal_count += 1
                print(f"  [{idx}/10] Query: '{q[:40]}...' -> Refused Correctly (Grounded: {res['grounded']})")
            else:
                print(f"  [{idx}/10] Query: '{q[:40]}...' -> FAILED TO REFUSE: '{res['answer'][:50]}...'")

    print(f"\nRefusal Score: {refusal_count}/10 (Target: 10/10)")
    assert refusal_count == 10, f"Expected 10/10 refusals, got {refusal_count}/10"
    print("=== Hallucination Refusal Benchmark Passed 100%! Zero Hallucinations. ===")

if __name__ == "__main__":
    asyncio.run(test_hallucination_refusal())
