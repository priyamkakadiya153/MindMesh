from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import ForeignKey, Text, String, Integer, JSON
from uuid import UUID
from typing import List, Optional
from .base import BaseEntity

class Message(BaseEntity):
    __tablename__ = "messages"

    chat_id: Mapped[UUID] = mapped_column(ForeignKey("chats.id", ondelete="CASCADE"), index=True, nullable=False)
    sender_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    organization_id: Mapped[UUID] = mapped_column(ForeignKey("organizations.id", ondelete="CASCADE"), index=True, nullable=False)
    role: Mapped[str] = mapped_column(String(20), nullable=False, default="user")
    content: Mapped[str] = mapped_column(Text, nullable=False)
    content_type: Mapped[str] = mapped_column(String(50), nullable=False, default="text/plain")
    model: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    token_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    latency_ms: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    msg_metadata: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    chat: Mapped["Chat"] = relationship(back_populates="messages")
    sender: Mapped["User"] = relationship()
    citations: Mapped[List["Citation"]] = relationship(back_populates="message", cascade="all, delete-orphan")

    @property
    def conversation_id(self) -> UUID:
        return self.chat_id

    @conversation_id.setter
    def conversation_id(self, value: UUID):
        self.chat_id = value
