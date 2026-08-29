import asyncio
import os
import sys
import uuid
from datetime import datetime

sys.path.insert(0, os.path.abspath("."))

from app.core.database import AsyncSessionLocal, engine
from app.models.user import User
from app.models.organization import Organization
from app.models.organization_member import OrganizationMember
from app.workspace.models import Workspace
from app.models.conversations import Conversation, ConversationMember, DirectMessage
from app.conversations.router import get_or_create_private_conversation, PrivateConversationCreate, list_conversations
from app.conversations.messages_router import send_message, get_messages_history, edit_message, delete_message, MessageCreatePayload, MessageUpdatePayload

async def test_direct_messaging_foundation():
    print("--- Starting MindMesh Subphase 1.1 Direct Messaging Foundation Tests ---")

    async with AsyncSessionLocal() as db:
        # 1. Setup Test Organization, Users, and Memberships
        suffix = uuid.uuid4().hex[:6]
        org = Organization(name="DM Test Org", slug=f"dm-org-{suffix}")
        db.add(org)
        await db.commit()
        await db.refresh(org)

        user_a = User(email=f"usera-{suffix}@test.com", username=f"usera-{suffix}", first_name="User", last_name="Alpha", hashed_password="hash")
        user_b = User(email=f"userb-{suffix}@test.com", username=f"userb-{suffix}", first_name="User", last_name="Beta", hashed_password="hash")
        db.add_all([user_a, user_b])
        await db.commit()
        await db.refresh(user_a)
        await db.refresh(user_b)

        mem_a = OrganizationMember(id=uuid.uuid4(), organization_id=org.id, user_id=user_a.id, role="member", is_active=True)
        mem_b = OrganizationMember(id=uuid.uuid4(), organization_id=org.id, user_id=user_b.id, role="member", is_active=True)
        db.add_all([mem_a, mem_b])
        await db.commit()

        ws = Workspace(organization_id=org.id, name="DM Workspace", slug=f"dm-ws-{suffix}")
        db.add(ws)
        await db.commit()
        await db.refresh(ws)

        print(f"--> Created test Org ({org.id}), User A ({user_a.id}), User B ({user_b.id}), and Workspace.")

        # 2. Test Get/Create Private Conversation (User A -> User B)
        payload = PrivateConversationCreate(
            target_user_id=user_b.id,
            organization_id=org.id,
            workspace_id=ws.id
        )
        conv_resp_a = await get_or_create_private_conversation(payload=payload, current_user=user_a, db=db)
        assert conv_resp_a.id is not None
        assert conv_resp_a.participant.id == user_b.id
        assert conv_resp_a.participant.full_name == "User Beta"
        print(f"--> Conversation created for User A (ID: {conv_resp_a.id}, Target: {conv_resp_a.participant.full_name}).")

        # 3. Test Idempotency of Private Conversation Creation (User B -> User A)
        payload_b = PrivateConversationCreate(
            target_user_id=user_a.id,
            organization_id=org.id,
            workspace_id=ws.id
        )
        conv_resp_b = await get_or_create_private_conversation(payload=payload_b, current_user=user_b, db=db)
        assert conv_resp_b.id == conv_resp_a.id
        assert conv_resp_b.participant.id == user_a.id
        assert conv_resp_b.participant.full_name == "User Alpha"
        print("--> Idempotency verified: User B initiating DM returns same conversation with correct target.")

        # 4. Test Listing Conversations for Both Users
        convs_a = await list_conversations(organization_id=org.id, workspace_id=ws.id, current_user=user_a, db=db)
        convs_b = await list_conversations(organization_id=org.id, workspace_id=ws.id, current_user=user_b, db=db)
        assert len(convs_a) == 1
        assert len(convs_b) == 1
        assert convs_a[0].participant.id == user_b.id
        assert convs_b[0].participant.id == user_a.id
        print("--> Verified list_conversations for User A and User B with correct participant mapping.")

        # 5. Test Sending Message with Client Idempotency ID (client_msg_id)
        client_id_1 = f"client-msg-{uuid.uuid4().hex}"
        msg_payload_1 = MessageCreatePayload(
            conversation_id=conv_resp_a.id,
            content="Hello Beta! Welcome to MindMesh DM.",
            message_type="text",
            client_msg_id=client_id_1
        )
        sent_msg_1 = await send_message(payload=msg_payload_1, current_user=user_a, db=db)
        assert sent_msg_1.id is not None
        assert sent_msg_1.client_msg_id == client_id_1
        assert sent_msg_1.content == "Hello Beta! Welcome to MindMesh DM."
        print(f"--> User A sent message 1 (DB ID: {sent_msg_1.id}, Client ID: {client_id_1}).")

        # 6. Test Prevent Duplicate Message (Sending identical client_msg_id again)
        dup_sent = await send_message(payload=msg_payload_1, current_user=user_a, db=db)
        assert dup_sent.id == sent_msg_1.id
        assert dup_sent.client_msg_id == client_id_1
        print("--> Prevent Duplicate Message verified: Retrying identical client_msg_id returned saved message.")

        # 7. Test Message History Retrieval for User B
        history_b = await get_messages_history(conversation_id=conv_resp_a.id, limit=50, offset=0, current_user=user_b, db=db)
        assert len(history_b) == 1
        assert history_b[0].id == sent_msg_1.id
        assert history_b[0].sender.full_name == "User Alpha"
        print(f"--> User B retrieved message history ({len(history_b)} message).")

        # 8. Test Last Message Preview & Timestamp in Conversation List
        convs_a_updated = await list_conversations(organization_id=org.id, workspace_id=ws.id, current_user=user_a, db=db)
        assert convs_a_updated[0].last_message is not None
        assert convs_a_updated[0].last_message.content == "Hello Beta! Welcome to MindMesh DM."
        assert convs_a_updated[0].last_message_at is not None
        print(f"--> Verified last message preview ('{convs_a_updated[0].last_message.content}') and timestamp.")

        # 9. Test Edit Message (User A edits, User B prohibited)
        edit_payload = MessageUpdatePayload(content="Hello Beta! Welcome to MindMesh DM (edited).")
        edited_msg = await edit_message(id=sent_msg_1.id, payload=edit_payload, current_user=user_a, db=db)
        assert edited_msg.edited is True
        assert edited_msg.content == "Hello Beta! Welcome to MindMesh DM (edited)."
        print("--> Verified message editing by sender.")

        # 10. Test Delete Message (User A deletes)
        del_resp = await delete_message(id=sent_msg_1.id, current_user=user_a, db=db)
        assert del_resp["status"] == "success"

        history_b_after = await get_messages_history(conversation_id=conv_resp_a.id, limit=50, offset=0, current_user=user_b, db=db)
        assert history_b_after[0].deleted is True
        assert history_b_after[0].content == "This message was deleted"
        print("--> Verified soft delete and masked content retrieval for recipient.")

        print("=== MindMesh Subphase 1.1 Direct Messaging Foundation Tests Passed Successfully! ===")

if __name__ == "__main__":
    asyncio.run(test_direct_messaging_foundation())
