"""CSV/Excel parser for bulk import of properties and POIs."""

from pathlib import Path
from typing import Any

import pandas as pd


# Default column mappings — keys are our internal field names, values are common CSV column names
PROPERTY_COLUMN_ALIASES: dict[str, list[str]] = {
    "title": ["title", "name", "listing_title", "property_name"],
    "description": ["description", "desc", "details"],
    "price": ["price", "asking_price", "listing_price", "precio"],
    "currency": ["currency", "curr"],
    "operation": ["operation", "type", "listing_type", "sale_rent"],
    "bedrooms": ["bedrooms", "beds", "num_bedrooms", "habitaciones"],
    "bathrooms": ["bathrooms", "baths", "num_bathrooms", "baños"],
    "area_m2": ["area_m2", "area", "size", "square_meters", "sqm", "superficie"],
    "address": ["address", "full_address", "street", "direccion"],
    "city": ["city", "ciudad", "town"],
    "postal_code": ["postal_code", "zip", "zipcode", "codigo_postal"],
    "latitude": ["latitude", "lat"],
    "longitude": ["longitude", "lng", "lon"],
    "external_id": ["external_id", "ref", "reference", "listing_id"],
}

POI_COLUMN_ALIASES: dict[str, list[str]] = {
    "name": ["name", "business_name", "poi_name", "nombre"],
    "category": ["category", "type", "category_name", "categoria"],
    "latitude": ["latitude", "lat"],
    "longitude": ["longitude", "lng", "lon"],
    "address": ["address", "full_address", "direccion"],
    "rating": ["rating", "stars", "score"],
}


def _resolve_columns(df: pd.DataFrame, aliases: dict[str, list[str]]) -> dict[str, str]:
    """Map CSV columns to internal field names using aliases.

    Returns:
        Dict mapping internal_field -> actual_csv_column_name.
    """
    df_cols_lower = {c.lower().strip(): c for c in df.columns}
    mapping = {}

    for field, possible_names in aliases.items():
        for alias in possible_names:
            if alias.lower() in df_cols_lower:
                mapping[field] = df_cols_lower[alias.lower()]
                break

    return mapping


def parse_file(filepath: str | Path) -> pd.DataFrame:
    """Read a CSV or Excel file into a DataFrame.

    Supports: .csv, .xlsx, .xls
    """
    filepath = Path(filepath)

    if filepath.suffix.lower() in (".xlsx", ".xls"):
        return pd.read_excel(filepath)
    elif filepath.suffix.lower() == ".csv":
        # Try common encodings
        for encoding in ("utf-8", "latin-1", "cp1252"):
            try:
                return pd.read_csv(filepath, encoding=encoding)
            except UnicodeDecodeError:
                continue
        raise ValueError(f"Could not decode CSV file: {filepath}")
    else:
        raise ValueError(f"Unsupported file format: {filepath.suffix}")


def parse_properties(filepath: str | Path) -> list[dict[str, Any]]:
    """Parse a CSV/Excel file into a list of property dicts.

    Automatically maps common column name variations to internal fields.

    Returns:
        List of dicts ready for PropertyService.bulk_create().
    """
    df = parse_file(filepath)
    col_map = _resolve_columns(df, PROPERTY_COLUMN_ALIASES)

    if not col_map:
        raise ValueError(
            f"Could not map any columns. Found: {list(df.columns)}. "
            f"Expected at least one of: {list(PROPERTY_COLUMN_ALIASES.keys())}"
        )

    records = []
    for _, row in df.iterrows():
        record = {}
        for field, csv_col in col_map.items():
            val = row.get(csv_col)
            if pd.notna(val):
                record[field] = val
        if record.get("title") or record.get("address"):
            records.append(record)

    return records


def parse_pois(filepath: str | Path) -> list[dict[str, Any]]:
    """Parse a CSV/Excel file into a list of POI/business dicts.

    Returns:
        List of dicts ready for POIService.bulk_create().
    """
    df = parse_file(filepath)
    col_map = _resolve_columns(df, POI_COLUMN_ALIASES)

    if not col_map:
        raise ValueError(
            f"Could not map any columns. Found: {list(df.columns)}. "
            f"Expected at least one of: {list(POI_COLUMN_ALIASES.keys())}"
        )

    records = []
    for _, row in df.iterrows():
        record = {}
        for field, csv_col in col_map.items():
            val = row.get(csv_col)
            if pd.notna(val):
                record[field] = val
        if record.get("name"):
            records.append(record)

    return records
