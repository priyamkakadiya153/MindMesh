import logging
from uuid import UUID
from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime
from sqlalchemy import select, update, func, desc, or_, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.chat import Chat
from app.models.message import Message
from app.models.citation import Citation
from app.models.user import User

logger = logging.getLogger(__name__)

class ChatSessionManager:
    # ---------------- CONVERSATION CRUD & REPOSITORY ----------------

    @staticmethod
    async def create_conversation(
        db: AsyncSession,
        organization_id: UUID,
        user_id: UUID,
        workspace_id: Optional[UUID] = None,
        title: Optional[str] = None,
        description: Optional[str] = None
    ) -> Chat:
        """Creates a new database-backed conversation."""
        chat = Chat(
            name=title or "New Conversation",
            description=description,
            organization_id=organization_id,
            user_id=user_id,
            workspace_id=workspace_id,
            is_pinned=False,
            status="active",
            last_message_at=datetime.utcnow(),
            settings={}
        )
        db.add(chat)
        await db.flush()
        return chat

    @staticmethod
    async def list_conversations(
        db: AsyncSession,
        organization_id: UUID,
        user_id: UUID,
        workspace_id: Optional[UUID] = None,
        page: int = 1,
        limit: int = 20,
        is_pinned: Optional[bool] = None,
        query: Optional[str] = None
    ) -> Tuple[List[Chat], int]:
        """Lists active (non-soft-deleted) conversations with pagination and isolation."""
        stmt = select(Chat).where(
            Chat.organization_id == organization_id,
            Chat.deleted_at.is_(None),
            Chat.is_active == True
        )

        # Enforce workspace / user isolation
        if workspace_id:
            stmt = stmt.where(Chat.workspace_id == workspace_id)
            
        stmt = stmt.where(or_(Chat.user_id == user_id, Chat.user_id.is_(None)))

        if is_pinned is not None:
            stmt = stmt.where(Chat.is_pinned == is_pinned)

        if query and query.strip():
            stmt = stmt.where(Chat.name.ilike(f"%{query.strip()}%"))

        # Count total matching rows
        count_stmt = select(func.count()).select_from(stmt.subquery())
        total_count = (await db.execute(count_stmt)).scalar() or 0

        # Paginate results ordered by last_message_at or created_at
        offset = (page - 1) * limit
        stmt = stmt.order_by(
            desc(Chat.is_pinned),
            desc(Chat.last_message_at),
            desc(Chat.created_at)
        ).offset(offset).limit(limit)

        res = await db.execute(stmt)
        chats = res.scalars().all()

        return chats, total_count

    @staticmethod
    async def get_conversation(
        db: AsyncSession,
        conversation_id: UUID,
        organization_id: UUID,
        user_id: Optional[UUID] = None
    ) -> Optional[Chat]:
        """Retrieves single conversation with workspace/org permission validation."""
        stmt = select(Chat).where(
            Chat.id == conversation_id,
            Chat.organization_id == organization_id,
            Chat.deleted_at.is_(None)
        )
        res = await db.execute(stmt)
        return res.scalar_one_or_none()

    @staticmethod
    async def update_conversation(
        db: AsyncSession,
        conversation_id: UUID,
        organization_id: UUID,
        user_id: UUID,
        title: Optional[str] = None,
        description: Optional[str] = None,
        is_pinned: Optional[bool] = None,
        status: Optional[str] = None,
        workspace_id: Optional[UUID] = None,
        settings: Optional[Dict[str, Any]] = None
    ) -> Optional[Chat]:
        """Updates properties of a conversation."""
        chat = await ChatSessionManager.get_conversation(db, conversation_id, organization_id, user_id)
        if not chat:
            return None

        if title is not None:
            chat.name = title
        if description is not None:
            chat.description = description
        if is_pinned is not None:
            chat.is_pinned = is_pinned
        if status is not None:
            chat.status = status
        if workspace_id is not None:
            chat.workspace_id = workspace_id
        if settings is not None:
            curr = chat.settings or {}
            curr.update(settings)
            chat.settings = curr

        chat.updated_at = datetime.utcnow()
        await db.flush()
        return chat

    @staticmethod
    async def set_pending_action(
        db: AsyncSession,
        chat_id: UUID,
        pending_data: Optional[Dict[str, Any]]
    ) -> None:
        """Stores or clears active pending action state in conversation settings."""
        stmt = select(Chat).where(Chat.id == chat_id)
        res = await db.execute(stmt)
        chat = res.scalar_one_or_none()
        if chat:
            curr = dict(chat.settings or {})
            if pending_data:
                curr["pending_action"] = pending_data
            else:
                curr.pop("pending_action", None)
            chat.settings = curr
            await db.flush()

    @staticmethod
    async def get_pending_action(
        db: AsyncSession,
        chat_id: UUID
    ) -> Optional[Dict[str, Any]]:
        """Retrieves active pending action state for a conversation."""
        stmt = select(Chat).where(Chat.id == chat_id)
        res = await db.execute(stmt)
        chat = res.scalar_one_or_none()
        if chat and chat.settings:
            return chat.settings.get("pending_action")
        return None

    @staticmethod
    async def soft_delete_conversation(
        db: AsyncSession,
        conversation_id: UUID,
        organization_id: UUID,
        user_id: Optional[UUID] = None
    ) -> bool:
        """Soft deletes a conversation setting deleted_at = now()."""
        chat = await ChatSessionManager.get_conversation(db, conversation_id, organization_id, user_id)
        if not chat:
            return False

        chat.deleted_at = datetime.utcnow()
        chat.is_active = False
        await db.flush()
        return True

    @staticmethod
    async def toggle_pin_conversation(
        db: AsyncSession,
        conversation_id: UUID,
        organization_id: UUID,
        user_id: UUID,
        is_pinned: bool
    ) -> Optional[Chat]:
        """Pins or unpins a conversation."""
        return await ChatSessionManager.update_conversation(
            db=db,
            conversation_id=conversation_id,
            organization_id=organization_id,
            user_id=user_id,
            is_pinned=is_pinned
        )

    @staticmethod
    async def search_conversations(
        db: AsyncSession,
        organization_id: UUID,
        user_id: UUID,
        query: str,
        workspace_id: Optional[UUID] = None,
        limit: int = 20
    ) -> List[Chat]:
        """Searches conversation titles for matching text."""
        chats, _ = await ChatSessionManager.list_conversations(
            db=db,
            organization_id=organization_id,
            user_id=user_id,
            workspace_id=workspace_id,
            page=1,
            limit=limit,
            query=query
        )
        return chats

    @staticmethod
    async def get_recent_conversations(
        db: AsyncSession,
        organization_id: UUID,
        user_id: UUID,
        workspace_id: Optional[UUID] = None,
        limit: int = 10
    ) -> List[Chat]:
        """Fetches top recent conversations ordered by last_message_at."""
        chats, _ = await ChatSessionManager.list_conversations(
            db=db,
            organization_id=organization_id,
            user_id=user_id,
            workspace_id=workspace_id,
            page=1,
            limit=limit
        )
        return chats

    # ---------------- MESSAGE REPOSITORY ----------------

    @staticmethod
    async def add_message(
        db: AsyncSession,
        conversation_id: UUID,
        sender_id: UUID,
        organization_id: UUID,
        content: str,
        role: str = "user",
        content_type: str = "text/plain",
        model: Optional[str] = None,
        token_count: int = 0,
        latency_ms: int = 0,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Message:
        """Stores a message immediately and updates parent conversation last_message_at timestamp."""
        msg = Message(
            chat_id=conversation_id,
            sender_id=sender_id,
            organization_id=organization_id,
            role=role,
            content=content,
            content_type=content_type,
            model=model,
            token_count=token_count,
            latency_ms=latency_ms,
            msg_metadata=metadata
        )
        db.add(msg)
        await db.flush()

        # Update last_message_at on conversation
        stmt = update(Chat).where(Chat.id == conversation_id).values(
            last_message_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        await db.execute(stmt)
        return msg

    @staticmethod
    async def list_messages(
        db: AsyncSession,
        conversation_id: UUID,
        organization_id: UUID,
        limit: int = 100
    ) -> List[Message]:
        """Lists non-deleted messages for a conversation ordered chronologically."""
        stmt = select(Message).where(
            Message.chat_id == conversation_id,
            Message.organization_id == organization_id,
            Message.deleted_at.is_(None)
        ).order_by(Message.created_at.asc()).limit(limit)

        res = await db.execute(stmt)
        return res.scalars().all()

    @staticmethod
    async def soft_delete_message(
        db: AsyncSession,
        message_id: UUID,
        organization_id: UUID
    ) -> bool:
        """Soft deletes a single message."""
        stmt = select(Message).where(
            Message.id == message_id,
            Message.organization_id == organization_id,
            Message.deleted_at.is_(None)
        )
        res = await db.execute(stmt)
        msg = res.scalar_one_or_none()
        if not msg:
            return False

        msg.deleted_at = datetime.utcnow()
        msg.is_active = False
        await db.flush()
        return True

    # ---------------- LEGACY & UTILITY METHODS ----------------

    @staticmethod
    async def get_or_create_session(
        db: AsyncSession,
        organization_id: UUID,
        user_id: Optional[UUID] = None,
        workspace_id: Optional[UUID] = None,
        chat_id: Optional[UUID] = None,
        name: Optional[str] = None
    ) -> Chat:
        """Backwards compatibility session resolver."""
        if chat_id:
            chat = await ChatSessionManager.get_conversation(db, chat_id, organization_id, user_id)
            if chat:
                if workspace_id and chat.workspace_id != workspace_id:
                    chat.workspace_id = workspace_id
                return chat

        return await ChatSessionManager.create_conversation(
            db=db,
            organization_id=organization_id,
            user_id=user_id or UUID("00000000-0000-0000-0000-000000000000"),
            workspace_id=workspace_id,
            title=name
        )

    @staticmethod
    async def get_assistant_user(db: AsyncSession) -> User:
        """Finds or creates system-wide AI Assistant user."""
        stmt = select(User).where(User.email == "assistant@mindmesh.ai")
        res = await db.execute(stmt)
        ai_user = res.scalar_one_or_none()
        if not ai_user:
            ai_user = User(
                username="ai_assistant",
                email="assistant@mindmesh.ai",
                hashed_password="system_assistant_password_hash"
            )
            db.add(ai_user)
            await db.flush()
        return ai_user

    @staticmethod
    async def save_user_message(
        db: AsyncSession,
        chat_id: UUID,
        sender_id: UUID,
        organization_id: UUID,
        content: str,
        client_message_id: Optional[str] = None
    ) -> Message:
        # Prevent accidental rapid double-click duplicate creation (< 2.0s window or matching client_message_id)
        stmt = select(Message).where(
            Message.chat_id == chat_id,
            Message.organization_id == organization_id,
            Message.deleted_at.is_(None)
        ).order_by(desc(Message.created_at)).limit(1)
        res = await db.execute(stmt)
        last_msg = res.scalar_one_or_none()

        if last_msg and last_msg.role == "user":
            if client_message_id and last_msg.msg_metadata and last_msg.msg_metadata.get("client_message_id") == client_message_id:
                return last_msg

            if last_msg.content == content:
                delta = (datetime.utcnow() - last_msg.created_at).total_seconds() if last_msg.created_at else 0.0
                if delta < 2.0:
                    return last_msg

        meta = {"client_message_id": client_message_id} if client_message_id else None

        return await ChatSessionManager.add_message(
            db=db,
            conversation_id=chat_id,
            sender_id=sender_id,
            organization_id=organization_id,
            role="user",
            content=content,
            metadata=meta
        )

    @classmethod
    async def save_assistant_message(
        cls,
        db: AsyncSession,
        chat_id: UUID,
        organization_id: UUID,
        content: str,
        model: Optional[str] = None,
        token_count: int = 0,
        latency_ms: int = 0,
        citations: Optional[List[Dict[str, Any]]] = None,
        msg_metadata: Optional[Dict[str, Any]] = None
    ) -> Message:
        ai_user = await cls.get_assistant_user(db)
        msg = await cls.add_message(
            db=db,
            conversation_id=chat_id,
            sender_id=ai_user.id,
            organization_id=organization_id,
            role="assistant",
            content=content,
            model=model,
            token_count=token_count,
            latency_ms=latency_ms,
            metadata=msg_metadata
        )

        if citations:
            for c in citations:
                doc_id = c.get("document_id") if isinstance(c, dict) else getattr(c, "document_id", None)
                chunk_id_val = c.get("chunk_id") if isinstance(c, dict) else getattr(c, "chunk_id", None)
                if doc_id and chunk_id_val:
                    try:
                        doc_uuid = UUID(str(doc_id))
                        chunk_uuid = UUID(str(chunk_id_val))
                        page_val = c.get("page") if isinstance(c, dict) else getattr(c, "page", getattr(c, "page_number", None))
                        score_val = c.get("score", 1.0) if isinstance(c, dict) else getattr(c, "score", 1.0)
                        ws_id = getattr(c, "workspace_id", None) or (msg.chat.workspace_id if msg.chat else None)
                        if ws_id:
                            cit_entity = Citation(
                                message_id=msg.id,
                                conversation_id=chat_id,
                                document_id=doc_uuid,
                                chunk_id=chunk_uuid,
                                organization_id=organization_id,
                                workspace_id=ws_id,
                                page_number=page_val or 1,
                                score=score_val or 1.0
                            )
                            db.add(cit_entity)
                    except Exception as err:
                        logger.warning(f"Could not persist citation record: {err}")
            try:
                await db.flush()
            except Exception as err:
                logger.warning(f"Failed to flush citation entities: {err}")

        return msg

    @staticmethod
    async def retry_assistant_generation(
        db: AsyncSession,
        message_id: UUID,
        organization_id: UUID,
        new_content: str,
        model: Optional[str] = None
    ) -> Optional[Message]:
        stmt = select(Message).where(
            Message.id == message_id,
            Message.organization_id == organization_id,
            Message.deleted_at.is_(None)
        )
        res = await db.execute(stmt)
        msg = res.scalar_one_or_none()
        if not msg:
            return None

        msg.content = new_content
        if model:
            msg.model = model
        msg.msg_metadata = msg.msg_metadata or {}
        msg.msg_metadata["retried"] = True
        msg.msg_metadata["retried_at"] = datetime.utcnow().isoformat()
        await db.flush()
        return msg

    @staticmethod
    async def regenerate_assistant_response(
        db: AsyncSession,
        conversation_id: UUID,
        organization_id: UUID,
        new_content: str,
        model: Optional[str] = None
    ) -> Optional[Message]:
        # Find latest assistant message for conversation
        stmt = select(Message).where(
            Message.chat_id == conversation_id,
            Message.organization_id == organization_id,
            Message.role == "assistant",
            Message.deleted_at.is_(None)
        ).order_by(desc(Message.created_at)).limit(1)

        res = await db.execute(stmt)
        last_asst_msg = res.scalar_one_or_none()

        if last_asst_msg:
            last_asst_msg.content = new_content
            if model:
                last_asst_msg.model = model
            last_asst_msg.msg_metadata = last_asst_msg.msg_metadata or {}
            last_asst_msg.msg_metadata["regenerated"] = True
            last_asst_msg.msg_metadata["regenerated_at"] = datetime.utcnow().isoformat()
            await db.flush()
            return last_asst_msg
        else:
            ai_user = await ChatSessionManager.get_assistant_user(db)
            return await ChatSessionManager.add_message(
                db=db,
                conversation_id=conversation_id,
                sender_id=ai_user.id,
                organization_id=organization_id,
                role="assistant",
                content=new_content,
                model=model
            )


    @staticmethod
    async def delete_session(db: AsyncSession, chat_id: UUID) -> bool:
        """Alias for soft delete."""
        return await ChatSessionManager.soft_delete_conversation(
            db=db,
            conversation_id=chat_id,
            organization_id=UUID("00000000-0000-0000-0000-000000000000") # bypass org check for legacy route
        )
