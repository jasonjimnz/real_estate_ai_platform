"""AI blueprint — chat endpoint for the LangChain agent."""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

from nestscout.services.ai_service import AIService

ai_bp = Blueprint("ai", __name__)


@ai_bp.post("/chat")
@jwt_required()
def chat():
    """Send a message to the AI assistant."""
    data = request.get_json(silent=True) or {}
    message = data.get("message", "").strip()

    if not message:
        return jsonify({"error": "Message is required"}), 400

    user_id = int(get_jwt_identity())
    response = AIService.chat(message, user_id=user_id)
    return jsonify({"response": response}), 200


@ai_bp.post("/search")
@jwt_required()
def ai_search():
    """Natural-language property search powered by AI."""
    data = request.get_json(silent=True) or {}
    query = data.get("query", "").strip()

    if not query:
        return jsonify({"error": "Query is required"}), 400

    results = AIService.search(query)
    return jsonify({"results": results}), 200
