import asyncio
import sys
import os
from uuid import uuid4
from datetime import datetime

sys.path.insert(0, os.path.abspath("."))

from app.database.session import AsyncSessionLocal
from app.models.user import User
from app.models.organization import Organization
from app.models.organization_member import OrganizationMember
from app.models.workspace import Workspace
from app.models.conversations import Conversation, ConversationMember
from app.models.attachments import Attachment
from app.files.router import preview_file, download_file, verify_file_access
from fastapi import HTTPException, Request

class DummyRequest:
    client = None

async def run_dm_file_preview_download_test():
    print("==================================================")
    print("  PHASE 1.4B DM FILE PREVIEW & DOWNLOAD VERIFICATION")
    print("==================================================")

    now = datetime.utcnow()
    org_id = uuid4()
    ws_id = uuid4()
    user_a_id = uuid4()
    user_b_id = uuid4()
    user_c_id = uuid4()
    conv_id = uuid4()

    async with AsyncSessionLocal() as db:
        # Step 1: Create Users
        user_a = User(id=user_a_id, email=f"usera_{uuid4().hex[:6]}@mindmesh.io", username=f"usera_{uuid4().hex[:6]}", first_name="User", last_name="A", hashed_password="p", is_active=True, created_at=now, updated_at=now)
        user_b = User(id=user_b_id, email=f"userb_{uuid4().hex[:6]}@mindmesh.io", username=f"userb_{uuid4().hex[:6]}", first_name="User", last_name="B", hashed_password="p", is_active=True, created_at=now, updated_at=now)
        user_c = User(id=user_c_id, email=f"userc_{uuid4().hex[:6]}@mindmesh.io", username=f"userc_{uuid4().hex[:6]}", first_name="User", last_name="C", hashed_password="p", is_active=True, created_at=now, updated_at=now)
        db.add_all([user_a, user_b, user_c])
        await db.commit()

        # Step 2: Create Org & Workspace
        org = Organization(id=org_id, name="Preview Org", slug=f"prev-{uuid4().hex[:6]}", owner_id=user_a_id, created_at=now, updated_at=now)
        ws = Workspace(id=ws_id, organization_id=org_id, name="Preview WS", slug=f"ws-{uuid4().hex[:6]}", owner_id=user_a_id, created_at=now, updated_at=now)
        db.add_all([org, ws])
        await db.commit()

        # Step 3: Org Members
        db.add(OrganizationMember(id=uuid4(), organization_id=org_id, user_id=user_a_id, role="owner", is_active=True, joined_at=now))
        db.add(OrganizationMember(id=uuid4(), organization_id=org_id, user_id=user_b_id, role="member", is_active=True, joined_at=now))
        await db.commit()

        # Step 4: Private DM Conversation between A & B
        conv = Conversation(
            id=conv_id, organization_id=org_id, workspace_id=ws_id, type="private",
            participant_one=user_a_id, participant_two=user_b_id, created_at=now, updated_at=now
        )
        mem_a = ConversationMember(id=uuid4(), conversation_id=conv_id, user_id=user_a_id, role="member", joined_at=now)
        mem_b = ConversationMember(id=uuid4(), conversation_id=conv_id, user_id=user_b_id, role="member", joined_at=now)
        db.add_all([conv, mem_a, mem_b])
        await db.commit()

        # Step 5: Create dummy file on storage disk
        import os
        from app.storage.local_provider import default_storage_provider
        dummy_content = b"%PDF-1.4 Fake PDF Content for MindMesh Phase 1.4B Tests"
        storage_filename, relative_path = await default_storage_provider.save_file(dummy_content, "Project_Plan.pdf")

        att_id = uuid4()
        attachment = Attachment(
            id=att_id,
            organization_id=org_id,
            workspace_id=ws_id,
            conversation_id=conv_id,
            uploaded_by=user_a_id,
            original_filename="Project_Plan.pdf",
            storage_filename=storage_filename,
            mime_type="application/pdf",
            file_size=len(dummy_content),
            storage_path=relative_path,
            status="active",
            processing_status="ready",
            created_at=now,
            updated_at=now
        )
        db.add(attachment)
        await db.commit()
        print(f"[PASS] 1. Created DM Attachment: 'Project_Plan.pdf' (ID: {att_id})")

        req = DummyRequest()

        # Step 6: Authorized User B Previews Attachment
        prev_resp = await preview_file(att_id, request=req, current_user=user_b, db=db)
        assert prev_resp.media_type == "application/pdf"
        assert "inline" in prev_resp.headers["Content-Disposition"]
        print(f"[PASS] 2. Authorized User B previewed attachment inline (Content-Disposition: {prev_resp.headers['Content-Disposition']})")

        # Step 7: Authorized User B Downloads Attachment
        dl_resp = await download_file(att_id, request=req, current_user=user_b, db=db)
        assert "attachment" in dl_resp.headers["Content-Disposition"]
        print(f"[PASS] 3. Authorized User B downloaded attachment (Content-Disposition: {dl_resp.headers['Content-Disposition']})")

        # Step 8: Security Check — Unauthorized User C Preview Blocked
        try:
            await preview_file(att_id, request=req, current_user=user_c, db=db)
            assert False, "User C must be blocked from previewing DM attachment!"
        except HTTPException as e:
            assert e.status_code == 403
            print(f"[PASS] 4. Unauthorized User C preview blocked (Status 403: {e.detail})")

        # Step 9: Security Check — Unauthorized User C Download Blocked
        try:
            await download_file(att_id, request=req, current_user=user_c, db=db)
            assert False, "User C must be blocked from downloading DM attachment!"
        except HTTPException as e:
            assert e.status_code == 403
            print(f"[PASS] 5. Unauthorized User C download blocked (Status 403: {e.detail})")

    print("==================================================")
    print("  ALL DM PREVIEW & DOWNLOAD TESTS PASSED 100%!")
    print("==================================================")

if __name__ == "__main__":
    asyncio.run(run_dm_file_preview_download_test())
