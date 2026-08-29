from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, Column, ForeignKey, Table
from typing import List
from .base import BaseEntity
from ..database.base import Base

role_permissions = Table(
    "role_permissions",
    Base.metadata,
    Column("role_id", ForeignKey("roles.id", ondelete="CASCADE"), primary_key=True),
    Column("permission_id", ForeignKey("permissions.id", ondelete="CASCADE"), primary_key=True),
)

class Role(BaseEntity):
    __tablename__ = "roles"

    name: Mapped[str] = mapped_column(String, unique=True, index=True, nullable=False)
    description: Mapped[str] = mapped_column(String, nullable=True)

    permissions: Mapped[List["Permission"]] = relationship(
        "Permission",
        secondary=role_permissions,
        back_populates="roles"
    )
