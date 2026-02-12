"""Property service — CRUD, search, bulk operations."""

from typing import Any

from sqlalchemy import select

from nestscout.extensions import db
from nestscout.models.property import Property


class PropertyService:
    """Business logic for property management."""

    @staticmethod
    def create(data: dict[str, Any]) -> Property:
        """Create a single property from a dict."""
        prop = Property(**data)
        db.session.add(prop)
        db.session.commit()
        return prop

    @staticmethod
    def bulk_create(records: list[dict[str, Any]]) -> tuple[int, int]:
        """Bulk-create properties from a list of dicts.

        Skips duplicates based on external_id if present.

        Returns:
            Tuple of (created_count, skipped_count).
        """
        created = 0
        skipped = 0

        for record in records:
            # Deduplication by external_id
            ext_id = record.get("external_id")
            if ext_id:
                existing = db.session.execute(
                    select(Property).where(Property.external_id == ext_id)
                ).scalar_one_or_none()
                if existing:
                    skipped += 1
                    continue

            prop = Property(**record)
            db.session.add(prop)
            created += 1

        db.session.commit()
        return created, skipped

    @staticmethod
    def get_by_id(property_id: int) -> Property | None:
        return db.session.get(Property, property_id)

    @staticmethod
    def list_properties(
        city: str | None = None,
        operation: str | None = None,
        min_price: float | None = None,
        max_price: float | None = None,
        min_bedrooms: int | None = None,
        max_bedrooms: int | None = None,
        min_area: float | None = None,
        max_area: float | None = None,
        page: int = 1,
        per_page: int = 20,
    ) -> dict:
        """List properties with optional filters and pagination."""
        stmt = select(Property)

        if city:
            stmt = stmt.where(Property.city.ilike(f"%{city}%"))
        if operation:
            stmt = stmt.where(Property.operation == operation)
        if min_price is not None:
            stmt = stmt.where(Property.price >= min_price)
        if max_price is not None:
            stmt = stmt.where(Property.price <= max_price)
        if min_bedrooms is not None:
            stmt = stmt.where(Property.bedrooms >= min_bedrooms)
        if max_bedrooms is not None:
            stmt = stmt.where(Property.bedrooms <= max_bedrooms)
        if min_area is not None:
            stmt = stmt.where(Property.area_m2 >= min_area)
        if max_area is not None:
            stmt = stmt.where(Property.area_m2 <= max_area)

        # Count total
        from sqlalchemy import func
        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = db.session.execute(count_stmt).scalar()

        # Paginate
        stmt = stmt.order_by(Property.id.desc()).offset((page - 1) * per_page).limit(per_page)
        items = list(db.session.execute(stmt).scalars())

        return {
            "items": [p.to_dict() for p in items],
            "total": total,
            "page": page,
            "per_page": per_page,
            "pages": (total + per_page - 1) // per_page if total else 0,
        }

    @staticmethod
    def update(property_id: int, data: dict[str, Any]) -> Property | None:
        prop = db.session.get(Property, property_id)
        if not prop:
            return None
        for key, value in data.items():
            if hasattr(prop, key):
                setattr(prop, key, value)
        db.session.commit()
        return prop

    @staticmethod
    def delete(property_id: int) -> bool:
        prop = db.session.get(Property, property_id)
        if not prop:
            return False
        db.session.delete(prop)
        db.session.commit()
        return True
