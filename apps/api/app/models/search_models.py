from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import ForeignKey, String, Text, DateTime, JSON
from uuid import UUID, uuid4
from datetime import datetime
from typing import Optional, Dict, Any
from .base import BaseEntity

class SavedSearch(BaseEntity):
    __tablename__ = "saved_searches"

    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    organization_id: Mapped[UUID] = mapped_column(ForeignKey("organizations.id", ondelete="CASCADE"), index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    query_text: Mapped[str] = mapped_column(String(500), nullable=False)
    filters_json: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)


class RecentSearch(BaseEntity):
    __tablename__ = "recent_searches"

    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    organization_id: Mapped[UUID] = mapped_column(ForeignKey("organizations.id", ondelete="CASCADE"), index=True, nullable=False)
    query_text: Mapped[str] = mapped_column(String(500), nullable=False)
    searched_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
