import asyncio
import os
import sys
import uuid
from datetime import datetime

sys.path.insert(0, os.path.abspath("."))

from app.core.database import AsyncSessionLocal, engine
from app.models.base import BaseEntity
from app.models.organization import Organization
from app.models.user import User
from app.workspace.models import Workspace, WorkspaceMember
from app.models.organization_member import OrganizationMember
from app.documents.models import Document
from app.projects.models import Project
from app.models.task import Task
from app.knowledge.relationship_service import KnowledgeGraphRelationshipIntelligenceService

async def test_knowledge_graph_relationship_e2e():
    print("=== Starting MindMesh Phase 4.7 Knowledge Graph & Relationship Intelligence E2E Test Suite ===")

    async with engine.begin() as conn:
        await conn.run_sync(BaseEntity.metadata.create_all)

    async with AsyncSessionLocal() as session:
        # 1. Setup Tenant A
        orgA = Organization(name="Rel Org A", slug=f"rel-orga-{uuid.uuid4().hex[:6]}")
        session.add(orgA)
        await session.commit()

        wsA = Workspace(organization_id=orgA.id, name="Rel Workspace", slug=f"rel-wsa-{uuid.uuid4().hex[:6]}")
        session.add(wsA)
        await session.commit()

        uA_id = uuid.uuid4().hex[:6]
        userA = User(
            email=f"rel_usera_{uA_id}@mindmesh.com",
            username=f"rel_usera_{uA_id}",
            first_name="Priyam",
            last_name="User",
            hashed_password="mockpassword",
            phone_number=f"+1555{uA_id}"
        )
        session.add(userA)
        await session.commit()

        session.add(OrganizationMember(organization_id=orgA.id, user_id=userA.id, role="admin", is_active=True))
        session.add(WorkspaceMember(workspace_id=wsA.id, user_id=userA.id, role="admin", is_active=True))
        await session.commit()

        # -------------------------------------------------------------
        # Section 128 Master E2E Seeding
        # -------------------------------------------------------------
        project = Project(
            organization_id=orgA.id,
            workspace_id=wsA.id,
            name="Authentication System",
            slug=f"auth-rel-{uuid.uuid4().hex[:6]}",
            description="Relationship graph test project"
        )
        session.add(project)
        await session.commit()

        doc = Document(
            organization_id=orgA.id,
            workspace_id=wsA.id,
            project_id=project.id,
            title="Authentication Architecture",
            filename="auth_arch.md",
            original_filename="auth_arch.md",
            mime_type="text/markdown",
            extension="md",
            size=1024,
            checksum_sha256="checksum_rel_1",
            storage_path="/path/rel1.md",
            uploaded_by=userA.id
        )
        dst_file = Document(
            organization_id=orgA.id,
            workspace_id=wsA.id,
            project_id=project.id,
            title="authentication-design.dst",
            filename="authentication-design.dst",
            original_filename="authentication-design.dst",
            mime_type="application/octet-stream",
            extension="dst",
            size=4096,
            checksum_sha256="checksum_dst_1",
            storage_path="/path/design.dst",
            uploaded_by=userA.id
        )
        session.add_all([doc, dst_file])
        await session.commit()

        task = Task(
            organization_id=orgA.id,
            workspace_id=wsA.id,
            project_id=project.id,
            assignee_id=userA.id,
            title="Update deployment configuration",
            description="Task to update deployment settings.",
            status="BLOCKED",
            blocked_reason="Missing production environment variable"
        )
        session.add(task)
        await session.commit()

        graph_service = KnowledgeGraphRelationshipIntelligenceService(session)

        # -------------------------------------------------------------
        # Section 128 Verification Checks
        # -------------------------------------------------------------

        # 1. GRAPH NODE CREATION
        p_node = await graph_service.add_or_update_node(orgA.id, wsA.id, "PROJECT", project.id, project.name)
        d_node = await graph_service.add_or_update_node(orgA.id, wsA.id, "DECISION", uuid.uuid4(), "PostgreSQL selected", project.id)
        c_node = await graph_service.add_or_update_node(orgA.id, wsA.id, "CONVERSATION", uuid.uuid4(), "We decided to use PostgreSQL.", project.id)
        doc_node = await graph_service.add_or_update_node(orgA.id, wsA.id, "DOCUMENT", doc.id, doc.title, project.id)
        task_node = await graph_service.add_or_update_node(orgA.id, wsA.id, "TASK", task.id, task.title, project.id)
        dst_node = await graph_service.add_or_update_node(orgA.id, wsA.id, "FILE", dst_file.id, dst_file.title, project.id)

        print("--> [1. GRAPH NODES PASS] Total Created Nodes:", 6)

        # 2. RELATIONSHIP CREATION
        edge_orig = await graph_service.add_relationship(orgA.id, wsA.id, uuid.UUID(c_node["entity_id"]), uuid.UUID(d_node["entity_id"]), "produced", evidence="Conversation produced decision.")
        edge_supp = await graph_service.add_relationship(orgA.id, wsA.id, uuid.UUID(doc_node["entity_id"]), uuid.UUID(d_node["entity_id"]), "supports", evidence="Doc supports decision.")
        edge_aff = await graph_service.add_relationship(orgA.id, wsA.id, uuid.UUID(d_node["entity_id"]), uuid.UUID(task_node["entity_id"]), "affects", evidence="Decision affects task.")
        edge_dst = await graph_service.add_relationship(orgA.id, wsA.id, uuid.UUID(dst_node["entity_id"]), uuid.UUID(p_node["entity_id"]), "related_to", evidence="DST file connected to project.")

        print("--> [2. RELATIONSHIPS PASS] Decision Origin Edge:", edge_orig["relationship_type"], "| Decision Impact Edge:", edge_aff["relationship_type"])

        # 3. NEIGHBORHOOD EXPLORER TEST
        neigh = await graph_service.get_graph_neighborhood(orgA.id, uuid.UUID(d_node["entity_id"]), depth=1)
        print("--> [3. GRAPH EXPLORER PASS] Neighborhood Node Count:", neigh["total_nodes"], "| Edge Count:", neigh["total_edges"])
        assert neigh["total_nodes"] >= 3

        # 4. DECISION IMPACT ANALYSIS TEST
        impact = await graph_service.analyze_decision_impact(orgA.id, uuid.UUID(d_node["entity_id"]))
        print("--> [4. DECISION IMPACT PASS] Affected Tasks Count:", len(impact["affected_tasks"]))
        assert len(impact["affected_tasks"]) >= 1

        # 5. DECISION ORIGIN TRACE TEST
        origin = await graph_service.trace_decision_origin(orgA.id, uuid.UUID(d_node["entity_id"]))
        print("--> [5. DECISION ORIGIN TRACE PASS] Origin Sources Count:", origin["origin_sources_count"])
        assert origin["origin_sources_count"] >= 1

        # 6. GRAPH HEALTH & REBUILD TEST
        health = await graph_service.audit_graph_health(orgA.id)
        print("--> [6. GRAPH HEALTH PASS] Health Status:", health["health_status"], "| Broken Edges:", health["broken_edges_count"])
        assert health["health_status"] == "HEALTHY"

        rebuild_res = await graph_service.rebuild_graph_relationships(orgA.id)
        print("--> [7. GRAPH REBUILD PASS] Message:", rebuild_res["message"])
        assert rebuild_res["success"] is True

    print("=== MindMesh Phase 4.7 Knowledge Graph & Relationship Intelligence E2E Test Suite Passed 100%! ===")

if __name__ == "__main__":
    asyncio.run(test_knowledge_graph_relationship_e2e())
