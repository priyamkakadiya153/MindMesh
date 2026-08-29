from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, Integer, Float, ForeignKey, Text, JSON
from uuid import UUID
from typing import Optional
from ...models.base import BaseEntity

class WorkspaceAISetting(BaseEntity):
    __tablename__ = "workspace_ai_settings"

    workspace_id: Mapped[UUID] = mapped_column(ForeignKey("workspaces.id", ondelete="CASCADE"), index=True, nullable=False, unique=True)
    organization_id: Mapped[UUID] = mapped_column(ForeignKey("organizations.id", ondelete="CASCADE"), index=True, nullable=False)
    provider: Mapped[str] = mapped_column(String(50), nullable=False, default="gemini")
    model: Mapped[str] = mapped_column(String(100), nullable=False, default="gemini-2.5-flash")
    temperature: Mapped[float] = mapped_column(Float, nullable=False, default=0.7)
    top_p: Mapped[float] = mapped_column(Float, nullable=False, default=0.95)
    max_tokens: Mapped[int] = mapped_column(Integer, nullable=False, default=2048)
    fallback_provider: Mapped[str] = mapped_column(String(50), nullable=False, default="openai")
    fallback_model: Mapped[str] = mapped_column(String(100), nullable=False, default="gpt-4o-mini")
    system_prompt: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
