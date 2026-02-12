"""POI and POICategory models — points of interest near properties."""

from typing import Optional

from sqlalchemy import String, Float, Integer, JSON, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from nestscout.models.base import BaseModel


class POICategory(BaseModel):
    __tablename__ = "poi_categories"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    icon: Mapped[Optional[str]] = mapped_column(String(50))
    color: Mapped[Optional[str]] = mapped_column(String(7))  # hex color

    pois: Mapped[list["POI"]] = relationship(back_populates="category", lazy="dynamic")

    def __repr__(self) -> str:
        return f"<POICategory {self.name}>"

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "icon": self.icon,
            "color": self.color,
        }


class POI(BaseModel):
    __tablename__ = "pois"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    category_id: Mapped[int] = mapped_column(
        ForeignKey("poi_categories.id"), index=True, nullable=False
    )
    latitude: Mapped[Optional[float]] = mapped_column(Float)
    longitude: Mapped[Optional[float]] = mapped_column(Float)
    address: Mapped[Optional[str]] = mapped_column(String(500))
    rating: Mapped[Optional[float]] = mapped_column(Float)
    metadata_extra: Mapped[Optional[dict]] = mapped_column(JSON)

    # Relationships
    category: Mapped["POICategory"] = relationship(back_populates="pois")
    property_distances: Mapped[list["PropertyPOIDistance"]] = relationship(  # noqa: F821
        back_populates="poi", cascade="all, delete-orphan", lazy="dynamic",
    )

    def __repr__(self) -> str:
        return f"<POI {self.name}>"

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "category_id": self.category_id,
            "category_name": self.category.name if self.category else None,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "address": self.address,
            "rating": self.rating,
        }
