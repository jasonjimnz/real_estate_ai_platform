"""User model — authentication and profile."""

from typing import Optional

from sqlalchemy import String, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship

from nestscout.models.base import BaseModel


class User(BaseModel):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(120), unique=True, index=True, nullable=False)
    username: Mapped[str] = mapped_column(String(80), unique=True, index=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    role: Mapped[str] = mapped_column(String(20), default="user", nullable=False)  # user|contributor|admin

    # Relationships
    search_profiles: Mapped[list["SearchProfile"]] = relationship(  # noqa: F821
        back_populates="user", cascade="all, delete-orphan", lazy="dynamic",
    )
    saved_properties: Mapped[list["SavedProperty"]] = relationship(  # noqa: F821
        back_populates="user", cascade="all, delete-orphan", lazy="dynamic",
    )

    def __repr__(self) -> str:
        return f"<User {self.username}>"

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "email": self.email,
            "username": self.username,
            "is_active": self.is_active,
            "role": self.role,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
