"""DataSource model — tracks where properties come from."""

from typing import Optional

from sqlalchemy import String, Boolean, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from nestscout.models.base import BaseModel


class DataSource(BaseModel):
    __tablename__ = "data_sources"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    source_type: Mapped[str] = mapped_column(
        String(20), nullable=False
    )  # scraper | api | manual | csv
    config: Mapped[Optional[dict]] = mapped_column(JSON)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Relationships
    properties: Mapped[list["Property"]] = relationship(  # noqa: F821
        backref="data_source", lazy="dynamic",
    )

    def __repr__(self) -> str:
        return f"<DataSource {self.name} ({self.source_type})>"

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "source_type": self.source_type,
            "config": self.config,
            "is_active": self.is_active,
        }
