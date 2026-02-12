"""POIs blueprint — CRUD, categories, proximity search, bulk import."""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required

from nestscout.schemas.poi import POICreateSchema, POIBulkSchema, POICategorySchema
from nestscout.services.poi_service import POIService

pois_bp = Blueprint("pois", __name__)
_create_schema = POICreateSchema()
_bulk_schema = POIBulkSchema()
_category_schema = POICategorySchema()


@pois_bp.get("/")
def list_pois():
    """List POIs with optional category filter."""
    category_id = request.args.get("category_id", type=int)
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 50, type=int)

    result = POIService.list_pois(category_id=category_id, page=page, per_page=per_page)
    return jsonify(result), 200


@pois_bp.get("/nearby")
def nearby_pois():
    """Find POIs near a given point."""
    lat = request.args.get("lat", type=float)
    lng = request.args.get("lng", type=float)
    radius = request.args.get("radius", 1000, type=float)
    category_id = request.args.get("category_id", type=int)

    if lat is None or lng is None:
        return jsonify({"error": "lat and lng are required"}), 400

    results = POIService.find_nearby(lat, lng, radius_m=radius, category_id=category_id)
    return jsonify({"items": results, "total": len(results)}), 200


@pois_bp.get("/categories")
def list_categories():
    """List all POI categories."""
    cats = POIService.list_categories()
    return jsonify({"items": [c.to_dict() for c in cats]}), 200


@pois_bp.post("/categories")
@jwt_required()
def create_category():
    """Create a POI category."""
    errors = _category_schema.validate(request.get_json(silent=True) or {})
    if errors:
        return jsonify({"error": "Validation failed", "details": errors}), 400

    data = _category_schema.load(request.get_json())
    cat = POIService.get_or_create_category(**data)
    return jsonify({"message": "Category created", "category": cat.to_dict()}), 201


@pois_bp.post("/")
@jwt_required()
def create_poi():
    """Create a single POI/business."""
    errors = _create_schema.validate(request.get_json(silent=True) or {})
    if errors:
        return jsonify({"error": "Validation failed", "details": errors}), 400

    data = _create_schema.load(request.get_json())
    poi = POIService.create(data)
    return jsonify({"message": "POI created", "poi": poi.to_dict()}), 201


@pois_bp.post("/bulk")
@jwt_required()
def bulk_create_pois():
    """Bulk import POIs/businesses from a JSON array."""
    errors = _bulk_schema.validate(request.get_json(silent=True) or {})
    if errors:
        return jsonify({"error": "Validation failed", "details": errors}), 400

    data = _bulk_schema.load(request.get_json())
    created, skipped = POIService.bulk_create(data["pois"])
    return jsonify({
        "message": "Bulk import completed",
        "created": created,
        "skipped": skipped,
    }), 201
