"""POI service — CRUD, proximity search, bulk operations."""

from typing import Any

from sqlalchemy import select

from nestscout.extensions import db
from nestscout.models.poi import POI, POICategory
from nestscout.utils.geo import haversine_distance


class POIService:
    """Business logic for POI / business management."""

    # ── Categories ─────────────────────────────────────────────────────
    @staticmethod
    def get_or_create_category(name: str, icon: str | None = None, color: str | None = None) -> POICategory:
        """Get existing category by name or create a new one."""
        cat = db.session.execute(
            select(POICategory).where(POICategory.name == name)
        ).scalar_one_or_none()

        if cat:
            return cat

        cat = POICategory(name=name, icon=icon, color=color)
        db.session.add(cat)
        db.session.commit()
        return cat

    @staticmethod
    def list_categories() -> list[POICategory]:
        return list(db.session.execute(
            select(POICategory).order_by(POICategory.name)
        ).scalars())

    # ── POI CRUD ───────────────────────────────────────────────────────
    @staticmethod
    def create(data: dict[str, Any]) -> POI:
        """Create a single POI."""
        poi = POI(**data)
        db.session.add(poi)
        db.session.commit()
        return poi

    @staticmethod
    def bulk_create(records: list[dict[str, Any]]) -> tuple[int, int]:
        """Bulk-create POIs/businesses from a list of dicts.

        If a record contains 'category' (string) instead of 'category_id',
        the category is auto-resolved or created.

        Returns:
            Tuple of (created_count, skipped_count).
        """
        created = 0
        skipped = 0

        for record in records:
            # Resolve category name → category_id
            cat_name = record.pop("category", None)
            if cat_name and "category_id" not in record:
                cat = POIService.get_or_create_category(cat_name)
                record["category_id"] = cat.id

            if "category_id" not in record:
                skipped += 1
                continue

            poi = POI(**record)
            db.session.add(poi)
            created += 1

        db.session.commit()
        return created, skipped

    @staticmethod
    def get_by_id(poi_id: int) -> POI | None:
        return db.session.get(POI, poi_id)

    @staticmethod
    def list_pois(
        category_id: int | None = None,
        page: int = 1,
        per_page: int = 50,
    ) -> dict:
        """List POIs with optional category filter and pagination."""
        stmt = select(POI)
        if category_id:
            stmt = stmt.where(POI.category_id == category_id)

        from sqlalchemy import func
        total = db.session.execute(
            select(func.count()).select_from(stmt.subquery())
        ).scalar()

        stmt = stmt.order_by(POI.id).offset((page - 1) * per_page).limit(per_page)
        items = list(db.session.execute(stmt).scalars())

        return {
            "items": [p.to_dict() for p in items],
            "total": total,
            "page": page,
            "per_page": per_page,
        }

    @staticmethod
    def find_nearby(
        lat: float,
        lng: float,
        radius_m: float = 1000.0,
        category_id: int | None = None,
    ) -> list[dict]:
        """Find POIs within a radius of a point (haversine, SQLite-compatible).

        Returns:
            List of POI dicts with an added 'distance_m' field, sorted by distance.
        """
        stmt = select(POI).where(POI.latitude.isnot(None), POI.longitude.isnot(None))
        if category_id:
            stmt = stmt.where(POI.category_id == category_id)

        all_pois = list(db.session.execute(stmt).scalars())
        results = []

        for poi in all_pois:
            dist = haversine_distance(lat, lng, poi.latitude, poi.longitude)
            if dist <= radius_m:
                d = poi.to_dict()
                d["distance_m"] = round(dist, 1)
                results.append(d)

        results.sort(key=lambda x: x["distance_m"])
        return results
