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
from app.extensions.extension_platform_service import ExtensionPlatformService

async def test_extension_marketplace_master_e2e():
    print("=== Starting MindMesh Phase 6.29 Extension Marketplace Master E2E Test Suite ===")

    async with engine.begin() as conn:
        await conn.run_sync(BaseEntity.metadata.create_all)

    async with AsyncSessionLocal() as session:
        # 1. Setup Tenant & Auth
        org = Organization(name="Extension Org", slug=f"ext-org-{uuid.uuid4().hex[:6]}")
        session.add(org)
        await session.commit()

        ws = Workspace(organization_id=org.id, name="Extension Workspace", slug=f"ext-ws-{uuid.uuid4().hex[:6]}")
        session.add(ws)
        await session.commit()

        u_id = uuid.uuid4().hex[:6]
        user = User(
            email=f"ext_user_{u_id}@mindmesh.com",
            username=f"ext_user_{u_id}",
            first_name="Priyam",
            last_name="User",
            hashed_password="mockpassword",
            phone_number=f"+1555{u_id}",
            current_organization_id=org.id
        )
        session.add(user)
        await session.commit()

        session.add(OrganizationMember(organization_id=org.id, user_id=user.id, role="admin", is_active=True))
        session.add(WorkspaceMember(workspace_id=ws.id, user_id=user.id, role="admin", is_active=True))
        await session.commit()

        ext_service = ExtensionPlatformService(session)

        # -------------------------------------------------------------
        # Section 201 Verification Checks
        # -------------------------------------------------------------

        # 1. MARKETPLACE SEARCH & DISCOVERY TEST
        exts = await ext_service.list_marketplace_extensions("jira", None, org.id, user)
        print("--> [1. MARKETPLACE DISCOVERY PASS] Search Results:", len(exts), "| Found Extension:", exts[0]["name"])
        assert len(exts) == 1
        assert exts[0]["extension_id"] == "ext-jira-connector-01"

        # 2. PERMISSION REVIEW & ADMIN INSTALLATION TEST
        inst = await ext_service.install_extension("ext-jira-connector-01", org.id, user)
        print("--> [2. INSTALLATION PASS] Status:", inst["status"], "| Permissions Granted:", len(inst["permissions_granted"]))
        assert inst["status"] == "ENABLED"
        assert len(inst["permissions_granted"]) == 3

        # 3. KNOWLEDGE CONNECTOR INITIAL SYNC TEST
        sync_init = await ext_service.sync_knowledge_connector("ext-jira-connector-01", "INITIAL", org.id, user)
        print("--> [3. INITIAL SYNC PASS] Items Processed:", sync_init["items_processed"], "| Lineage Source:", sync_init["data_lineage"]["source"])
        assert sync_init["sync_status"] == "COMPLETED"
        assert sync_init["items_processed"] == 18

        # 4. INCREMENTAL SYNC & IDEMPOTENCY TEST
        sync_inc = await ext_service.sync_knowledge_connector("ext-jira-connector-01", "INCREMENTAL", org.id, user)
        print("--> [4. INCREMENTAL SYNC PASS] Created:", sync_inc["created_count"], "| Duplicates Prevented:", sync_inc["duplicates_prevented"])
        assert sync_inc["created_count"] == 0
        assert sync_inc["duplicates_prevented"] == 16

        # 5. CHANGE & CONFLICT RESOLUTION TEST
        print("--> [5. CONFLICT RESOLUTION PASS] Conflicts Detected:", len(sync_inc["conflicts_detected"]), "| Resolution:", sync_inc["conflicts_detected"][0]["resolution"])
        assert sync_inc["conflicts_detected"][0]["status"] == "RESOLVED"

        # 6. CUSTOM AGENT BUILDER PIPELINE TEST
        builder = await ext_service.build_custom_agent(
            name="Release Risk Analyst",
            role="Evaluates SOC2 compliance & deployment risk before release",
            capabilities=["RISK_ASSESSMENT", "COMPLIANCE_AUDIT"],
            instructions="Inspect Project Alpha specs and flag any unresolved security dependencies.",
            visibility="WORKSPACE",
            organization_id=org.id,
            user=user
        )
        print("--> [6. CUSTOM AGENT BUILDER PASS] Agent ID:", builder["agent_id"], "| Status:", builder["status"], "| Permissions:", len(builder["permissions_assigned"]))
        assert builder["status"] == "PUBLISHED"

        # 7. EMERGENCY DISABLE & PERMISSION REVOCATION TEST
        revoke = await ext_service.revoke_extension_permissions("ext-jira-connector-01", "Admin Emergency Security Disablement", org.id, user)
        print("--> [7. PERMISSION REVOCATION PASS] Status:", revoke["status"], "| Execution Blocked:", revoke["execution_requests_blocked"])
        assert revoke["status"] == "SUSPENDED"
        assert revoke["execution_requests_blocked"] is True

    print("=== MindMesh Phase 6.29 Extension Marketplace Master E2E Test Suite Passed 100%! ===")

if __name__ == "__main__":
    asyncio.run(test_extension_marketplace_master_e2e())
