from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import ForeignKey, String, Text, Boolean, Integer, DateTime, UniqueConstraint
from uuid import UUID, uuid4
from datetime import datetime
from typing import Optional, List
from .base import BaseEntity

class MessageReaction(BaseEntity):
    __tablename__ = "message_reactions"
    __table_args__ = (
        UniqueConstraint("message_id", "user_id", "emoji", name="uq_message_user_emoji"),
    )

    message_id: Mapped[UUID] = mapped_column(ForeignKey("direct_messages.id", ondelete="CASCADE"), index=True, nullable=False)
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    emoji: Mapped[str] = mapped_column(String(30), nullable=False)

    user: Mapped["User"] = relationship("User")


class MessageMention(BaseEntity):
    __tablename__ = "message_mentions"

    message_id: Mapped[UUID] = mapped_column(ForeignKey("direct_messages.id", ondelete="CASCADE"), index=True, nullable=False)
    mentioned_user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    conversation_id: Mapped[UUID] = mapped_column(ForeignKey("conversations.id", ondelete="CASCADE"), index=True, nullable=False)

    mentioned_user: Mapped["User"] = relationship("User")


class PinnedMessage(BaseEntity):
    __tablename__ = "pinned_messages"
    __table_args__ = (
        UniqueConstraint("conversation_id", "message_id", name="uq_conversation_pinned_message"),
    )

    conversation_id: Mapped[UUID] = mapped_column(ForeignKey("conversations.id", ondelete="CASCADE"), index=True, nullable=False)
    message_id: Mapped[UUID] = mapped_column(ForeignKey("direct_messages.id", ondelete="CASCADE"), index=True, nullable=False)
    pinned_by: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    pinned_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)

    pinned_by_user: Mapped["User"] = relationship("User")


class FavoriteConversation(BaseEntity):
    __tablename__ = "favorite_conversations"
    __table_args__ = (
        UniqueConstraint("user_id", "conversation_id", name="uq_user_favorite_conversation"),
    )

    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    conversation_id: Mapped[UUID] = mapped_column(ForeignKey("conversations.id", ondelete="CASCADE"), index=True, nullable=False)


class MessageDraft(BaseEntity):
    __tablename__ = "message_drafts"
    __table_args__ = (
        UniqueConstraint("user_id", "conversation_id", name="uq_user_conversation_draft"),
    )

    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    conversation_id: Mapped[UUID] = mapped_column(ForeignKey("conversations.id", ondelete="CASCADE"), index=True, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
