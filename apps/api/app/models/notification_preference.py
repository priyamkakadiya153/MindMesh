from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Boolean, ForeignKey
from uuid import UUID
from .base import BaseEntity

class NotificationPreference(BaseEntity):
    __tablename__ = "notification_preferences"

    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    mentions: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    project_updates: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    workspace_updates: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    marketing: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    user: Mapped["User"] = relationship()
