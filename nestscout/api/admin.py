"""Admin blueprint — platform stats and data source management."""

from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required
from sqlalchemy import select, func

from nestscout.extensions import db
from nestscout.models.user import User
from nestscout.models.property import Property
from nestscout.models.poi import POI, POICategory
from nestscout.models.data_source import DataSource

admin_bp = Blueprint("admin", __name__)


@admin_bp.get("/stats")
@jwt_required()
def platform_stats():
    """Get platform-wide statistics."""
    stats = {
        "users": db.session.execute(select(func.count(User.id))).scalar(),
        "properties": db.session.execute(select(func.count(Property.id))).scalar(),
        "pois": db.session.execute(select(func.count(POI.id))).scalar(),
        "categories": db.session.execute(select(func.count(POICategory.id))).scalar(),
        "data_sources": db.session.execute(select(func.count(DataSource.id))).scalar(),
    }
    return jsonify(stats), 200


@admin_bp.get("/sources")
@jwt_required()
def list_data_sources():
    """List all data sources."""
    sources = list(db.session.execute(
        select(DataSource).order_by(DataSource.id)
    ).scalars())
    return jsonify({"items": [s.to_dict() for s in sources]}), 200
