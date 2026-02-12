"""Profiles blueprint — search profile & scoring rule management."""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from sqlalchemy import select

from nestscout.extensions import db
from nestscout.models.search_profile import SearchProfile
from nestscout.models.scoring import ScoringRule
from nestscout.schemas.profile import ProfileCreateSchema, ProfileUpdateRulesSchema

profiles_bp = Blueprint("profiles", __name__)
_create_schema = ProfileCreateSchema()
_rules_schema = ProfileUpdateRulesSchema()


@profiles_bp.get("/")
@jwt_required()
def list_profiles():
    """List current user's search profiles."""
    user_id = int(get_jwt_identity())
    profiles = list(db.session.execute(
        select(SearchProfile).where(SearchProfile.user_id == user_id)
    ).scalars())
    return jsonify({"items": [p.to_dict(include_rules=True) for p in profiles]}), 200


@profiles_bp.post("/")
@jwt_required()
def create_profile():
    """Create a new search profile."""
    errors = _create_schema.validate(request.get_json(silent=True) or {})
    if errors:
        return jsonify({"error": "Validation failed", "details": errors}), 400

    data = _create_schema.load(request.get_json())
    user_id = int(get_jwt_identity())

    profile = SearchProfile(user_id=user_id, **data)
    db.session.add(profile)
    db.session.commit()
    return jsonify({"message": "Profile created", "profile": profile.to_dict()}), 201


@profiles_bp.get("/<int:profile_id>")
@jwt_required()
def get_profile(profile_id: int):
    """Get a specific search profile with its rules."""
    user_id = int(get_jwt_identity())
    profile = db.session.get(SearchProfile, profile_id)

    if not profile or profile.user_id != user_id:
        return jsonify({"error": "Profile not found"}), 404

    return jsonify(profile.to_dict(include_rules=True)), 200


@profiles_bp.put("/<int:profile_id>/rules")
@jwt_required()
def update_rules(profile_id: int):
    """Replace all scoring rules for a profile."""
    user_id = int(get_jwt_identity())
    profile = db.session.get(SearchProfile, profile_id)

    if not profile or profile.user_id != user_id:
        return jsonify({"error": "Profile not found"}), 404

    errors = _rules_schema.validate(request.get_json(silent=True) or {})
    if errors:
        return jsonify({"error": "Validation failed", "details": errors}), 400

    data = _rules_schema.load(request.get_json())

    # Delete existing rules
    for rule in profile.scoring_rules:
        db.session.delete(rule)

    # Create new rules
    for rule_data in data["rules"]:
        rule = ScoringRule(profile_id=profile_id, **rule_data)
        db.session.add(rule)

    db.session.commit()
    return jsonify({"message": "Rules updated", "profile": profile.to_dict(include_rules=True)}), 200


@profiles_bp.delete("/<int:profile_id>")
@jwt_required()
def delete_profile(profile_id: int):
    """Delete a search profile and all its rules/scores."""
    user_id = int(get_jwt_identity())
    profile = db.session.get(SearchProfile, profile_id)

    if not profile or profile.user_id != user_id:
        return jsonify({"error": "Profile not found"}), 404

    db.session.delete(profile)
    db.session.commit()
    return jsonify({"message": "Profile deleted"}), 200
