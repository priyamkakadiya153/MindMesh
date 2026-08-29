from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, Text, ForeignKey, JSON, DateTime, Index
from uuid import UUID, uuid4
from datetime import datetime
from typing import Optional, Any
from .base import BaseEntity

class SearchIndex(BaseEntity):
    __tablename__ = "search_index"

    entity_type: Mapped[str] = mapped_column(String(50), index=True, nullable=False)
    entity_id: Mapped[UUID] = mapped_column(index=True, nullable=False)
    workspace_id: Mapped[Optional[UUID]] = mapped_column(ForeignKey("workspaces.id", ondelete="CASCADE"), index=True, nullable=True)
    organization_id: Mapped[Optional[UUID]] = mapped_column(ForeignKey("organizations.id", ondelete="CASCADE"), index=True, nullable=True)
    owner_id: Mapped[Optional[UUID]] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), index=True, nullable=True)
    
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    content: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    tags: Mapped[Optional[Any]] = mapped_column(JSON, nullable=True, default=list)
    metadata_json: Mapped[Optional[Any]] = mapped_column(JSON, nullable=True, default=dict)

    __table_args__ = (
        Index("idx_search_index_org_ws_type", "organization_id", "workspace_id", "entity_type"),
    )

class SearchHistory(BaseEntity):
    __tablename__ = "search_history"

    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    query: Mapped[str] = mapped_column(String(255), nullable=False)

    __table_args__ = (
        Index("idx_search_history_user_created", "user_id", "created_at"),
    )
