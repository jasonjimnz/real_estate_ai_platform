"""Scoring models — ScoringRule and PropertyScore."""

from datetime import datetime
from typing import Optional

from sqlalchemy import String, Integer, Float, JSON, DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from nestscout.extensions import db
from nestscout.models.base import BaseModel


class ScoringRule(BaseModel):
    __tablename__ = "scoring_rules"

    id: Mapped[int] = mapped_column(primary_key=True)
    profile_id: Mapped[int] = mapped_column(ForeignKey("search_profiles.id"), index=True, nullable=False)

    rule_type: Mapped[str] = mapped_column(
        String(30), nullable=False
    )  # poi_proximity | poi_density | property_attr | walkability | ai_sentiment | price_value

    poi_category_id: Mapped[Optional[int]] = mapped_column(ForeignKey("poi_categories.id"))
    max_distance_m: Mapped[Optional[float]] = mapped_column(Float)
    weight: Mapped[float] = mapped_column(Float, default=0.1, nullable=False)  # 0.0–1.0
    parameters: Mapped[Optional[dict]] = mapped_column(JSON)

    # Relationships
    profile: Mapped["SearchProfile"] = relationship(back_populates="scoring_rules")  # noqa: F821

    def __repr__(self) -> str:
        return f"<ScoringRule {self.rule_type} w={self.weight}>"

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "profile_id": self.profile_id,
            "rule_type": self.rule_type,
            "poi_category_id": self.poi_category_id,
            "max_distance_m": self.max_distance_m,
            "weight": self.weight,
            "parameters": self.parameters,
        }


class PropertyScore(db.Model):
    """Materialised score for a property×profile pair."""

    __tablename__ = "property_scores"

    property_id: Mapped[int] = mapped_column(ForeignKey("properties.id"), primary_key=True)
    profile_id: Mapped[int] = mapped_column(ForeignKey("search_profiles.id"), primary_key=True)
    total_score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    breakdown: Mapped[Optional[dict]] = mapped_column(JSON)
    computed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False,
    )

    # Relationships
    property: Mapped["Property"] = relationship(back_populates="scores")  # noqa: F821
    profile: Mapped["SearchProfile"] = relationship(back_populates="property_scores")  # noqa: F821

    def __repr__(self) -> str:
        return f"<PropertyScore prop={self.property_id} prof={self.profile_id} score={self.total_score:.1f}>"

    def to_dict(self) -> dict:
        return {
            "property_id": self.property_id,
            "profile_id": self.profile_id,
            "total_score": self.total_score,
            "breakdown": self.breakdown,
            "computed_at": self.computed_at.isoformat() if self.computed_at else None,
        }
