"""Property model — real estate listing."""

from typing import Optional

from sqlalchemy import String, Text, Numeric, Integer, Float, JSON, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from nestscout.models.base import BaseModel


class Property(BaseModel):
    __tablename__ = "properties"

    id: Mapped[int] = mapped_column(primary_key=True)
    external_id: Mapped[Optional[str]] = mapped_column(String(255), unique=True, index=True)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    price: Mapped[Optional[float]] = mapped_column(Numeric(12, 2))
    currency: Mapped[str] = mapped_column(String(3), default="EUR", nullable=False)
    operation: Mapped[str] = mapped_column(String(10), default="sale", nullable=False)  # sale|rent
    bedrooms: Mapped[Optional[int]] = mapped_column(Integer)
    bathrooms: Mapped[Optional[int]] = mapped_column(Integer)
    area_m2: Mapped[Optional[float]] = mapped_column(Float)
    address: Mapped[Optional[str]] = mapped_column(String(500))
    city: Mapped[Optional[str]] = mapped_column(String(100), index=True)
    postal_code: Mapped[Optional[str]] = mapped_column(String(20))

    # Location — float columns work everywhere (SQLite + Postgres)
    latitude: Mapped[Optional[float]] = mapped_column(Float)
    longitude: Mapped[Optional[float]] = mapped_column(Float)

    # Flexible metadata from different sources
    raw_metadata: Mapped[Optional[dict]] = mapped_column(JSON)

    # Foreign keys
    data_source_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("data_sources.id"), index=True
    )

    # Relationships
    images: Mapped[list["PropertyImage"]] = relationship(  # noqa: F821
        back_populates="property", cascade="all, delete-orphan", lazy="selectin",
    )
    poi_distances: Mapped[list["PropertyPOIDistance"]] = relationship(  # noqa: F821
        back_populates="property", cascade="all, delete-orphan", lazy="dynamic",
    )
    scores: Mapped[list["PropertyScore"]] = relationship(  # noqa: F821
        back_populates="property", cascade="all, delete-orphan", lazy="dynamic",
    )
    saved_by: Mapped[list["SavedProperty"]] = relationship(  # noqa: F821
        back_populates="property", cascade="all, delete-orphan", lazy="dynamic",
    )

    def __repr__(self) -> str:
        return f"<Property {self.id}: {self.title[:40]}>"

    def to_dict(self, include_images: bool = False) -> dict:
        result = {
            "id": self.id,
            "external_id": self.external_id,
            "title": self.title,
            "description": self.description,
            "price": float(self.price) if self.price else None,
            "currency": self.currency,
            "operation": self.operation,
            "bedrooms": self.bedrooms,
            "bathrooms": self.bathrooms,
            "area_m2": self.area_m2,
            "address": self.address,
            "city": self.city,
            "postal_code": self.postal_code,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "data_source_id": self.data_source_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
        if include_images:
            result["images"] = [img.to_dict() for img in self.images]
        return result
