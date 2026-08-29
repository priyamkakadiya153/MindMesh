from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, Boolean, ForeignKey, DateTime
from uuid import UUID
from datetime import datetime
from ..database.base import Base

class UserSettings(Base):
    __tablename__ = "user_settings"

    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    theme: Mapped[str] = mapped_column(String(20), default="dark", nullable=False) # light, dark, system
    language: Mapped[str] = mapped_column(String(10), default="en", nullable=False)
    timezone: Mapped[str] = mapped_column(String(50), default="UTC", nullable=False)
    email_notifications: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    in_app_notifications: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    mentions: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    project_updates: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    privacy_level: Mapped[str] = mapped_column(String(20), default="standard", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    user: Mapped["User"] = relationship()

