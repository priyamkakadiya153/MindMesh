from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, Text, ForeignKey, Boolean, JSON, DateTime
from uuid import UUID
from datetime import datetime
from typing import List, Optional
from .base import BaseEntity

class Chat(BaseEntity):
    __tablename__ = "chats"

    name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    user_id: Mapped[Optional[UUID]] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=True)
    organization_id: Mapped[UUID] = mapped_column(ForeignKey("organizations.id", ondelete="CASCADE"), index=True, nullable=False)
    workspace_id: Mapped[Optional[UUID]] = mapped_column(ForeignKey("workspaces.id", ondelete="CASCADE"), index=True, nullable=True)
    is_pinned: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="active")
    last_message_at: Mapped[Optional[datetime]] = mapped_column(DateTime, index=True, nullable=True)
    settings: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    messages: Mapped[List["Message"]] = relationship(back_populates="chat", cascade="all, delete-orphan")
    user: Mapped[Optional["User"]] = relationship()

    @property
    def title(self) -> str:
        return self.name or "Untitled Conversation"

    @title.setter
    def title(self, value: str):
        self.name = value
