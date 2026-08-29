from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import ForeignKey, String, Text, Boolean, Integer, DateTime, UniqueConstraint
from uuid import UUID, uuid4
from datetime import datetime
from typing import Optional, List
from .base import BaseEntity

class Conversation(BaseEntity):
    __tablename__ = "conversations"

    organization_id: Mapped[UUID] = mapped_column(ForeignKey("organizations.id", ondelete="CASCADE"), index=True, nullable=False)
    workspace_id: Mapped[Optional[UUID]] = mapped_column(ForeignKey("workspaces.id", ondelete="CASCADE"), index=True, nullable=True)
    project_id: Mapped[Optional[UUID]] = mapped_column(ForeignKey("projects.id", ondelete="SET NULL"), index=True, nullable=True)
    
    type: Mapped[str] = mapped_column(String(30), nullable=False, default="private", index=True) # private, group, project_channel, announcement
    name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    avatar_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    owner_id: Mapped[Optional[UUID]] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), index=True, nullable=True)
    visibility: Mapped[str] = mapped_column(String(30), nullable=False, default="private") # public, private, read_only, announcement
    is_archived: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    archived_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    
    participant_one: Mapped[Optional[UUID]] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=True)
    participant_two: Mapped[Optional[UUID]] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=True)
    
    last_message_id: Mapped[Optional[UUID]] = mapped_column(ForeignKey("direct_messages.id", ondelete="SET NULL"), nullable=True)
    last_message_at: Mapped[Optional[datetime]] = mapped_column(DateTime, index=True, nullable=True)
    
    created_by_user_id: Mapped[Optional[UUID]] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    members: Mapped[List["ConversationMember"]] = relationship(back_populates="conversation", cascade="all, delete-orphan")
    messages: Mapped[List["DirectMessage"]] = relationship(back_populates="conversation", cascade="all, delete-orphan", foreign_keys="DirectMessage.conversation_id")
    last_message: Mapped[Optional["DirectMessage"]] = relationship("DirectMessage", foreign_keys=[last_message_id])
    owner_user: Mapped[Optional["User"]] = relationship("User", foreign_keys=[owner_id])
    participant_one_user: Mapped[Optional["User"]] = relationship("User", foreign_keys=[participant_one])
    participant_two_user: Mapped[Optional["User"]] = relationship("User", foreign_keys=[participant_two])



class ConversationMember(BaseEntity):
    __tablename__ = "conversation_members"
    __table_args__ = (UniqueConstraint("conversation_id", "user_id", name="uq_conv_member"),)

    conversation_id: Mapped[UUID] = mapped_column(ForeignKey("conversations.id", ondelete="CASCADE"), index=True, nullable=False)
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    
    role: Mapped[str] = mapped_column(String(20), nullable=False, default="member") # member, admin, owner
    joined_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
    
    last_read_message_id: Mapped[Optional[UUID]] = mapped_column(ForeignKey("direct_messages.id", ondelete="SET NULL"), nullable=True)
    last_read_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    unread_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    
    is_muted: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    is_pinned: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    conversation: Mapped["Conversation"] = relationship(back_populates="members")
    user: Mapped["User"] = relationship("User")


class DirectMessage(BaseEntity):
    __tablename__ = "direct_messages"

    conversation_id: Mapped[UUID] = mapped_column(ForeignKey("conversations.id", ondelete="CASCADE"), index=True, nullable=False)
    sender_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    organization_id: Mapped[UUID] = mapped_column(ForeignKey("organizations.id", ondelete="CASCADE"), index=True, nullable=False)
    workspace_id: Mapped[Optional[UUID]] = mapped_column(ForeignKey("workspaces.id", ondelete="CASCADE"), index=True, nullable=True)
    
    message_type: Mapped[str] = mapped_column(String(30), nullable=False, default="text") # text, system
    content: Mapped[str] = mapped_column(Text, nullable=False)
    reply_to_id: Mapped[Optional[UUID]] = mapped_column(ForeignKey("direct_messages.id", ondelete="SET NULL"), nullable=True)
    thread_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    last_reply_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    forwarded_from_id: Mapped[Optional[UUID]] = mapped_column(ForeignKey("direct_messages.id", ondelete="SET NULL"), nullable=True)
    
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="sent") # sending, sent, delivered, read, failed
    edited: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    deleted: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    client_msg_id: Mapped[Optional[str]] = mapped_column(String(255), index=True, nullable=True)

    conversation: Mapped["Conversation"] = relationship(back_populates="messages", foreign_keys=[conversation_id])
    sender: Mapped["User"] = relationship("User", foreign_keys=[sender_id])
    reads: Mapped[List["MessageRead"]] = relationship(back_populates="message", cascade="all, delete-orphan")
    reply_to_message: Mapped[Optional["DirectMessage"]] = relationship("DirectMessage", remote_side="DirectMessage.id", foreign_keys=[reply_to_id])
    reactions: Mapped[List["MessageReaction"]] = relationship("MessageReaction", cascade="all, delete-orphan")



class MessageRead(BaseEntity):
    __tablename__ = "message_reads"

    message_id: Mapped[UUID] = mapped_column(ForeignKey("direct_messages.id", ondelete="CASCADE"), index=True, nullable=False)
    conversation_id: Mapped[UUID] = mapped_column(ForeignKey("conversations.id", ondelete="CASCADE"), index=True, nullable=False)
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    read_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)

    message: Mapped["DirectMessage"] = relationship(back_populates="reads")
    user: Mapped["User"] = relationship("User")


class TypingStatus(BaseEntity):
    __tablename__ = "typing_status"

    conversation_id: Mapped[UUID] = mapped_column(ForeignKey("conversations.id", ondelete="CASCADE"), index=True, nullable=False)
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    is_typing: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)


class UserPresence(BaseEntity):
    __tablename__ = "user_presence"

    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), unique=True, index=True, nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="offline") # online, away, busy, offline
    custom_status: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    last_seen: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
