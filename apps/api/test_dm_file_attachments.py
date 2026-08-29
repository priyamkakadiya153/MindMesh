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
from app.files.router import verify_file_access
from fastapi import HTTPException

async def run_dm_file_attachments_test():
    print("==================================================")
    print("  PHASE 1.4A DM FILE ATTACHMENTS VERIFICATION")
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
        org = Organization(id=org_id, name="DM Attachment Org", slug=f"dm-att-{uuid4().hex[:6]}", owner_id=user_a_id, created_at=now, updated_at=now)
        ws = Workspace(id=ws_id, organization_id=org_id, name="DM Attachment WS", slug=f"ws-{uuid4().hex[:6]}", owner_id=user_a_id, created_at=now, updated_at=now)
        db.add_all([org, ws])
        await db.commit()

        # Step 3: Org Members
        db.add(OrganizationMember(id=uuid4(), organization_id=org_id, user_id=user_a_id, role="owner", is_active=True, joined_at=now))
        db.add(OrganizationMember(id=uuid4(), organization_id=org_id, user_id=user_b_id, role="member", is_active=True, joined_at=now))
        await db.commit()

        # Step 4: Private DM Conversation
        conv = Conversation(
            id=conv_id, organization_id=org_id, workspace_id=ws_id, type="private",
            participant_one=user_a_id, participant_two=user_b_id, created_at=now, updated_at=now
        )
        mem_a = ConversationMember(id=uuid4(), conversation_id=conv_id, user_id=user_a_id, role="member", joined_at=now)
        mem_b = ConversationMember(id=uuid4(), conversation_id=conv_id, user_id=user_b_id, role="member", joined_at=now)
        db.add_all([conv, mem_a, mem_b])
        await db.commit()
        print(f"[PASS] 1. Created DM Conversation between User A & User B (ID: {conv_id})")

        # Step 5: Upload Attachment Record for User A
        att_id = uuid4()
        attachment = Attachment(
            id=att_id,
            organization_id=org_id,
            workspace_id=ws_id,
            conversation_id=conv_id,
            uploaded_by=user_a_id,
            original_filename="Quarterly_Report.pdf",
            storage_filename=f"att_{uuid4().hex}.pdf",
            mime_type="application/pdf",
            file_size=2456789,
            storage_path="uploads/test/Quarterly_Report.pdf",
            status="active",
            processing_status="ready",
            created_at=now,
            updated_at=now
        )
        db.add(attachment)
        await db.commit()
        print(f"[PASS] 2. Uploaded Attachment Record: '{attachment.original_filename}' (ID: {att_id})")

        # Step 6: Send Message with Attachment
        send_payload = MessageCreatePayload(
            conversation_id=conv_id,
            content="Here is the quarterly report PDF.",
            attachment_ids=[att_id]
        )
        msg_resp = await send_message(send_payload, current_user=user_a, db=db)
        assert msg_resp.attachments is not None
        assert len(msg_resp.attachments) == 1
        assert msg_resp.attachments[0].id == att_id
        assert msg_resp.attachments[0].original_filename == "Quarterly_Report.pdf"
        print(f"[PASS] 3. Sent DM Message with Attachment: Msg ID {msg_resp.id}")

        # Step 7: Recipient User B Fetches Message History
        history = await get_messages_history(conv_id, current_user=user_b, db=db)
        assert len(history) == 1
        target_msg = history[0]
        assert target_msg.attachments is not None
        assert target_msg.attachments[0].original_filename == "Quarterly_Report.pdf"
        print(f"[PASS] 4. Recipient User B retrieved message history with attachment metadata")

        # Step 8: User B Authorization Check on Attachment
        await verify_file_access(db, attachment, user_b_id)
        print(f"[PASS] 5. Participant User B authorized to access DM attachment")

        # Step 9: Unauthorized User C Access Check
        try:
            await verify_file_access(db, attachment, user_c_id)
            assert False, "Unauthorized User C should not have access!"
        except HTTPException as e:
            assert e.status_code == 403
            print(f"[PASS] 6. Unauthorized User C Access Blocked (Status 403: {e.detail})")

    print("==================================================")
    print("  ALL DM FILE ATTACHMENT TESTS PASSED 100%!")
    print("==================================================")

if __name__ == "__main__":
    asyncio.run(run_dm_file_attachments_test())
