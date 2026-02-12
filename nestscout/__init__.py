"""NestScout — AI-powered real estate intelligence platform."""

from flask import Flask

from nestscout.config import config_by_name
from nestscout.extensions import db, migrate, jwt, ma, cors


def create_app(config_name: str | None = None) -> Flask:
    """Application factory — creates and configures the Flask app.

    Args:
        config_name: One of 'development', 'production', 'testing'.
                     Falls back to NESTSCOUT_ENV env var, then 'development'.
    """
    import os

    if config_name is None:
        config_name = os.getenv("NESTSCOUT_ENV", "development")

    app = Flask(__name__, instance_relative_config=True)
    app.config.from_object(config_by_name[config_name])

    # Ensure instance folder exists (SQLite lives here in dev)
    os.makedirs(app.instance_path, exist_ok=True)

    # --- Extensions ---
    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    ma.init_app(app)
    cors.init_app(app)

    # --- Blueprints ---
    _register_blueprints(app)

    # --- Error handlers ---
    _register_error_handlers(app)

    # --- Shell context ---
    @app.shell_context_processor
    def make_shell_context():
        from nestscout import models  # noqa: F811
        return {"db": db, "models": models}

    return app


def _register_blueprints(app: Flask) -> None:
    """Import and register all API blueprints."""
    from nestscout.api.auth import auth_bp
    from nestscout.api.properties import properties_bp
    from nestscout.api.pois import pois_bp
    from nestscout.api.profiles import profiles_bp
    from nestscout.api.scores import scores_bp
    from nestscout.api.imports import import_bp
    from nestscout.api.ai import ai_bp
    from nestscout.api.admin import admin_bp

    app.register_blueprint(auth_bp, url_prefix="/api/auth")
    app.register_blueprint(properties_bp, url_prefix="/api/properties")
    app.register_blueprint(pois_bp, url_prefix="/api/pois")
    app.register_blueprint(profiles_bp, url_prefix="/api/profiles")
    app.register_blueprint(scores_bp, url_prefix="/api/scores")
    app.register_blueprint(import_bp, url_prefix="/api/import")
    app.register_blueprint(ai_bp, url_prefix="/api/ai")
    app.register_blueprint(admin_bp, url_prefix="/api/admin")


def _register_error_handlers(app: Flask) -> None:
    """Register JSON error handlers for common HTTP errors."""
    from flask import jsonify

    @app.errorhandler(400)
    def bad_request(e):
        return jsonify({"error": "Bad request", "message": str(e)}), 400

    @app.errorhandler(404)
    def not_found(e):
        return jsonify({"error": "Not found", "message": str(e)}), 404

    @app.errorhandler(422)
    def unprocessable(e):
        return jsonify({"error": "Unprocessable entity", "message": str(e)}), 422

    @app.errorhandler(500)
    def internal_error(e):
        return jsonify({"error": "Internal server error"}), 500
