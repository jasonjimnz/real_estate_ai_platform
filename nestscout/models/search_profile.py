"""SearchProfile model — user-defined scoring profiles."""

from typing import Optional

from sqlalchemy import String, Integer, JSON, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from nestscout.models.base import BaseModel


class SearchProfile(BaseModel):
    __tablename__ = "search_profiles"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    filters: Mapped[Optional[dict]] = mapped_column(JSON)  # price range, city, etc.

    # Relationships
    user: Mapped["User"] = relationship(back_populates="search_profiles")  # noqa: F821
    scoring_rules: Mapped[list["ScoringRule"]] = relationship(  # noqa: F821
        back_populates="profile", cascade="all, delete-orphan", lazy="selectin",
    )
    property_scores: Mapped[list["PropertyScore"]] = relationship(  # noqa: F821
        back_populates="profile", cascade="all, delete-orphan", lazy="dynamic",
    )

    def __repr__(self) -> str:
        return f"<SearchProfile {self.name} (user={self.user_id})>"

    def to_dict(self, include_rules: bool = False) -> dict:
        result = {
            "id": self.id,
            "user_id": self.user_id,
            "name": self.name,
            "filters": self.filters,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
        if include_rules:
            result["scoring_rules"] = [r.to_dict() for r in self.scoring_rules]
        return result
