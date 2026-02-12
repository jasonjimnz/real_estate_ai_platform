"""Association models — PropertyPOIDistance, SavedProperty, PropertyImage."""

from datetime import datetime
from typing import Optional

from sqlalchemy import String, Integer, Float, Text, DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from nestscout.extensions import db
from nestscout.models.base import BaseModel


class PropertyPOIDistance(db.Model):
    """Pre-computed distance between a property and a nearby POI."""

    __tablename__ = "property_poi_distances"

    property_id: Mapped[int] = mapped_column(ForeignKey("properties.id"), primary_key=True)
    poi_id: Mapped[int] = mapped_column(ForeignKey("pois.id"), primary_key=True)
    distance_m: Mapped[float] = mapped_column(Float, nullable=False)
    walk_time_min: Mapped[Optional[float]] = mapped_column(Float)

    # Relationships
    property: Mapped["Property"] = relationship(back_populates="poi_distances")  # noqa: F821
    poi: Mapped["POI"] = relationship(back_populates="property_distances")  # noqa: F821

    def __repr__(self) -> str:
        return f"<Distance prop={self.property_id}→poi={self.poi_id}: {self.distance_m:.0f}m>"

    def to_dict(self) -> dict:
        return {
            "property_id": self.property_id,
            "poi_id": self.poi_id,
            "distance_m": self.distance_m,
            "walk_time_min": self.walk_time_min,
        }


class SavedProperty(db.Model):
    """User's bookmarked/saved properties."""

    __tablename__ = "saved_properties"

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), primary_key=True)
    property_id: Mapped[int] = mapped_column(ForeignKey("properties.id"), primary_key=True)
    notes: Mapped[Optional[str]] = mapped_column(Text)
    saved_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False,
    )

    # Relationships
    user: Mapped["User"] = relationship(back_populates="saved_properties")  # noqa: F821
    property: Mapped["Property"] = relationship(back_populates="saved_by")  # noqa: F821

    def to_dict(self) -> dict:
        return {
            "user_id": self.user_id,
            "property_id": self.property_id,
            "notes": self.notes,
            "saved_at": self.saved_at.isoformat() if self.saved_at else None,
        }


class PropertyImage(BaseModel):
    """Images associated with a property listing."""

    __tablename__ = "property_images"

    id: Mapped[int] = mapped_column(primary_key=True)
    property_id: Mapped[int] = mapped_column(ForeignKey("properties.id"), index=True, nullable=False)
    url: Mapped[str] = mapped_column(String(1000), nullable=False)
    position: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # Relationships
    property: Mapped["Property"] = relationship(back_populates="images")  # noqa: F821

    def __repr__(self) -> str:
        return f"<PropertyImage {self.id} pos={self.position}>"

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "property_id": self.property_id,
            "url": self.url,
            "position": self.position,
        }
