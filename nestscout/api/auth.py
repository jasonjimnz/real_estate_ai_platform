"""Auth blueprint — register, login, refresh tokens."""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

from nestscout.schemas.auth import RegisterSchema, LoginSchema
from nestscout.services.auth_service import AuthService

auth_bp = Blueprint("auth", __name__)
_register_schema = RegisterSchema()
_login_schema = LoginSchema()


@auth_bp.post("/register")
def register():
    """Register a new user account."""
    errors = _register_schema.validate(request.get_json(silent=True) or {})
    if errors:
        return jsonify({"error": "Validation failed", "details": errors}), 400

    data = _register_schema.load(request.get_json())
    try:
        user = AuthService.register(
            username=data["username"],
            email=data["email"],
            password=data["password"],
        )
        return jsonify({"message": "User created", "user": user.to_dict()}), 201
    except ValueError as e:
        return jsonify({"error": str(e)}), 409


@auth_bp.post("/login")
def login():
    """Authenticate and receive JWT tokens."""
    errors = _login_schema.validate(request.get_json(silent=True) or {})
    if errors:
        return jsonify({"error": "Validation failed", "details": errors}), 400

    data = _login_schema.load(request.get_json())
    try:
        tokens = AuthService.login(email=data["email"], password=data["password"])
        return jsonify(tokens), 200
    except ValueError as e:
        return jsonify({"error": str(e)}), 401


@auth_bp.get("/me")
@jwt_required()
def me():
    """Get current user profile."""
    user_id = int(get_jwt_identity())
    user = AuthService.get_user_by_id(user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404
    return jsonify({"user": user.to_dict()}), 200
