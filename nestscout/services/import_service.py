"""Import service — CSV/Excel parsing and ingestion pipeline."""

from pathlib import Path
from typing import Any

from nestscout.services.property_service import PropertyService
from nestscout.services.poi_service import POIService
from nestscout.utils.csv_parser import parse_properties, parse_pois


class ImportService:
    """Handles bulk import pipelines for properties and POIs."""

    @staticmethod
    def import_properties_csv(
        filepath: str | Path,
        defaults: dict[str, Any] | None = None,
    ) -> dict:
        """Import properties from a CSV/Excel file.

        Args:
            filepath: Path to the file.
            defaults: Default values to apply to all records (e.g. currency, city).

        Returns:
            Summary dict with counts and any errors.
        """
        try:
            records = parse_properties(filepath)
        except ValueError as e:
            return {"success": False, "error": str(e), "created": 0, "skipped": 0}

        # Apply defaults
        if defaults:
            for record in records:
                for key, value in defaults.items():
                    if key not in record or not record[key]:
                        record[key] = value

        created, skipped = PropertyService.bulk_create(records)

        return {
            "success": True,
            "total_parsed": len(records),
            "created": created,
            "skipped": skipped,
        }

    @staticmethod
    def import_pois_csv(
        filepath: str | Path,
        defaults: dict[str, Any] | None = None,
    ) -> dict:
        """Import POIs/businesses from a CSV/Excel file.

        Args:
            filepath: Path to the file.
            defaults: Default values to apply to all records.

        Returns:
            Summary dict with counts and any errors.
        """
        try:
            records = parse_pois(filepath)
        except ValueError as e:
            return {"success": False, "error": str(e), "created": 0, "skipped": 0}

        # Apply defaults
        if defaults:
            for record in records:
                for key, value in defaults.items():
                    if key not in record or not record[key]:
                        record[key] = value

        created, skipped = POIService.bulk_create(records)

        return {
            "success": True,
            "total_parsed": len(records),
            "created": created,
            "skipped": skipped,
        }
