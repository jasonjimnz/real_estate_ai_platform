"""Import blueprint — CSV/Excel upload and URL-based import."""

import os
import tempfile

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required

from nestscout.services.import_service import ImportService

import_bp = Blueprint("import", __name__)


@import_bp.post("/csv/properties")
@jwt_required()
def import_properties_csv():
    """Upload a CSV/Excel file to bulk-import properties."""
    if "file" not in request.files:
        return jsonify({"error": "No file provided. Use 'file' form field."}), 400

    file = request.files["file"]
    if not file.filename:
        return jsonify({"error": "Empty filename"}), 400

    # Save to temp file
    suffix = os.path.splitext(file.filename)[1]
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        file.save(tmp.name)
        tmp_path = tmp.name

    try:
        defaults = {
            "currency": request.form.get("currency", "EUR"),
            "operation": request.form.get("operation", "sale"),
            "city": request.form.get("city"),
        }
        defaults = {k: v for k, v in defaults.items() if v}

        result = ImportService.import_properties_csv(tmp_path, defaults=defaults)
        status = 201 if result["success"] else 400
        return jsonify(result), status
    finally:
        os.unlink(tmp_path)


@import_bp.post("/csv/pois")
@jwt_required()
def import_pois_csv():
    """Upload a CSV/Excel file to bulk-import POIs/businesses."""
    if "file" not in request.files:
        return jsonify({"error": "No file provided. Use 'file' form field."}), 400

    file = request.files["file"]
    if not file.filename:
        return jsonify({"error": "Empty filename"}), 400

    suffix = os.path.splitext(file.filename)[1]
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        file.save(tmp.name)
        tmp_path = tmp.name

    try:
        result = ImportService.import_pois_csv(tmp_path)
        status = 201 if result["success"] else 400
        return jsonify(result), status
    finally:
        os.unlink(tmp_path)
