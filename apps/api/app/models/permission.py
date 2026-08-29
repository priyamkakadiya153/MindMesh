from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, Text, Boolean, DateTime
from uuid import UUID
from datetime import datetime
from typing import List, Optional
from .base import BaseEntity
from .role import role_permissions

class Permission(BaseEntity):
    __tablename__ = "permissions"

    name: Mapped[str] = mapped_column(String, unique=True, index=True, nullable=False)
    description: Mapped[str] = mapped_column(String, nullable=True)

    roles: Mapped[List["Role"]] = relationship(
        "Role",
        secondary=role_permissions,
        back_populates="permissions"
    )


class PermissionRole(BaseEntity):
    __tablename__ = "permission_roles"

    name: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    level: Mapped[str] = mapped_column(String(50), default="organization", nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)


class PermissionMatrix(BaseEntity):
    __tablename__ = "permission_matrix"

    role_name: Mapped[str] = mapped_column(String(50), nullable=False)
    permission_key: Mapped[str] = mapped_column(String(100), nullable=False)
    is_granted: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
