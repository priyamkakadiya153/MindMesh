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
from app.conversations.messages_router import send_message, get_messages_history, MessageCreatePayload
from app.files.router import preview_file, download_file, verify_file_access
from app.storage.local_provider import default_storage_provider
from fastapi import HTTPException, Request

class DummyRequest:
    client = None

async def run_dm_embroidery_dst_test():
    print("==================================================")
    print("  PHASE 1.4C REAL DST EMBROIDERY FILE VERIFICATION")
    print("==================================================")

    real_dst_path = r"storage/uploads/attachments/d9/d957ada31845452abe0a7bd1fa6040b2.dst"
    if not os.path.exists(real_dst_path):
        print(f"[ERROR] Real DST test file not found at {real_dst_path}")
        return

    with open(real_dst_path, "rb") as f:
        real_dst_bytes = f.read()

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
        org = Organization(id=org_id, name="Embroidery Org", slug=f"emb-{uuid4().hex[:6]}", owner_id=user_a_id, created_at=now, updated_at=now)
        ws = Workspace(id=ws_id, organization_id=org_id, name="Embroidery WS", slug=f"ws-{uuid4().hex[:6]}", owner_id=user_a_id, created_at=now, updated_at=now)
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

        # Step 5: Save DST bytes via storage provider
        storage_filename, relative_path = await default_storage_provider.save_file(real_dst_bytes, "5_6334362792006524774.DST")

        att_id = uuid4()
        attachment = Attachment(
            id=att_id,
            organization_id=org_id,
            workspace_id=ws_id,
            conversation_id=conv_id,
            uploaded_by=user_a_id,
            original_filename="5_6334362792006524774.DST",
            storage_filename=storage_filename,
            mime_type="application/octet-stream", # Standard generic browser MIME type for DST
            file_size=len(real_dst_bytes),
            storage_path=relative_path,
            status="active",
            processing_status="ready",
            created_at=now,
            updated_at=now
        )
        db.add(attachment)
        await db.commit()
        print(f"[PASS] 1. Saved Real DST File: '5_6334362792006524774.DST' ({len(real_dst_bytes)} bytes, MIME: application/octet-stream)")

        # Step 6: Send Message with DST Attachment
        send_payload = MessageCreatePayload(
            conversation_id=conv_id,
            content="Here is the Tajima DST embroidery design file.",
            attachment_ids=[att_id]
        )
        msg_resp = await send_message(send_payload, current_user=user_a, db=db)
        assert msg_resp.attachments is not None
        assert msg_resp.attachments[0].id == att_id
        assert msg_resp.attachments[0].original_filename == "5_6334362792006524774.DST"
        print(f"[PASS] 2. Sent DM Message with DST Attachment: Msg ID {msg_resp.id}")

        # Step 7: Recipient User B Fetches History & Previews DST
        history = await get_messages_history(conv_id, current_user=user_b, db=db)
        assert len(history) == 1
        assert history[0].attachments[0].original_filename == "5_6334362792006524774.DST"
        print(f"[PASS] 3. Recipient User B fetched DM history containing DST attachment metadata")

        req = DummyRequest()
        prev_resp = await preview_file(att_id, request=req, current_user=user_b, db=db)
        assert len(prev_resp.body) == len(real_dst_bytes)
        print(f"[PASS] 4. Recipient User B previewed DST binary stream ({len(prev_resp.body)} bytes)")

        # Step 8: Security Check — Unauthorized User C Blocked
        try:
            await preview_file(att_id, request=req, current_user=user_c, db=db)
            assert False, "User C must be blocked from previewing DST attachment!"
        except HTTPException as e:
            assert e.status_code == 403
            print(f"[PASS] 5. Unauthorized User C preview blocked (Status 403: {e.detail})")

    print("==================================================")
    print("  ALL REAL DST EMBROIDERY TESTS PASSED 100%!")
    print("==================================================")

if __name__ == "__main__":
    asyncio.run(run_dm_embroidery_dst_test())
