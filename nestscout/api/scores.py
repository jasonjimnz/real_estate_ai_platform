"""Scores blueprint — retrieve and trigger score computation."""

from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

from nestscout.extensions import db
from nestscout.models.search_profile import SearchProfile
from nestscout.services.scoring_service import ScoringService

scores_bp = Blueprint("scores", __name__)


@scores_bp.get("/<int:profile_id>")
@jwt_required()
def get_scores(profile_id: int):
    """Get properties ranked by score for a given profile."""
    user_id = int(get_jwt_identity())
    profile = db.session.get(SearchProfile, profile_id)

    if not profile or profile.user_id != user_id:
        return jsonify({"error": "Profile not found"}), 404

    ranked = ScoringService.get_ranked_properties(profile_id)
    return jsonify({"items": ranked, "total": len(ranked)}), 200


@scores_bp.post("/<int:profile_id>/compute")
@jwt_required()
def compute_scores(profile_id: int):
    """Trigger score computation for a profile."""
    user_id = int(get_jwt_identity())
    profile = db.session.get(SearchProfile, profile_id)

    if not profile or profile.user_id != user_id:
        return jsonify({"error": "Profile not found"}), 404

    count = ScoringService.compute_scores(profile_id)
    return jsonify({"message": f"Scored {count} properties", "count": count}), 200
