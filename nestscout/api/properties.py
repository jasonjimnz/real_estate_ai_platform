"""Properties blueprint — CRUD + bulk import + filtered search."""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required

from nestscout.schemas.property import PropertyCreateSchema, PropertyBulkSchema, PropertyFilterSchema
from nestscout.services.property_service import PropertyService

properties_bp = Blueprint("properties", __name__)
_create_schema = PropertyCreateSchema()
_bulk_schema = PropertyBulkSchema()
_filter_schema = PropertyFilterSchema()


@properties_bp.get("/")
def list_properties():
    """List properties with optional filters and pagination."""
    errors = _filter_schema.validate(request.args)
    if errors:
        return jsonify({"error": "Invalid filters", "details": errors}), 400

    filters = _filter_schema.load(request.args)
    result = PropertyService.list_properties(**filters)
    return jsonify(result), 200


@properties_bp.get("/<int:property_id>")
def get_property(property_id: int):
    """Get a single property by ID."""
    prop = PropertyService.get_by_id(property_id)
    if not prop:
        return jsonify({"error": "Property not found"}), 404
    return jsonify(prop.to_dict(include_images=True)), 200


@properties_bp.post("/")
@jwt_required()
def create_property():
    """Create a single property."""
    errors = _create_schema.validate(request.get_json(silent=True) or {})
    if errors:
        return jsonify({"error": "Validation failed", "details": errors}), 400

    data = _create_schema.load(request.get_json())
    prop = PropertyService.create(data)
    return jsonify({"message": "Property created", "property": prop.to_dict()}), 201


@properties_bp.post("/bulk")
@jwt_required()
def bulk_create_properties():
    """Bulk import properties from a JSON array."""
    errors = _bulk_schema.validate(request.get_json(silent=True) or {})
    if errors:
        return jsonify({"error": "Validation failed", "details": errors}), 400

    data = _bulk_schema.load(request.get_json())
    created, skipped = PropertyService.bulk_create(data["properties"])
    return jsonify({
        "message": "Bulk import completed",
        "created": created,
        "skipped": skipped,
    }), 201


@properties_bp.put("/<int:property_id>")
@jwt_required()
def update_property(property_id: int):
    """Update a property."""
    data = request.get_json(silent=True) or {}
    prop = PropertyService.update(property_id, data)
    if not prop:
        return jsonify({"error": "Property not found"}), 404
    return jsonify({"message": "Updated", "property": prop.to_dict()}), 200


@properties_bp.delete("/<int:property_id>")
@jwt_required()
def delete_property(property_id: int):
    """Delete a property."""
    if PropertyService.delete(property_id):
        return jsonify({"message": "Deleted"}), 200
    return jsonify({"error": "Property not found"}), 404
