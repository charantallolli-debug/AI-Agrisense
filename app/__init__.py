"""
Flask application factory.

Usage:
    from app import create_app
    app = create_app("development")
"""
import logging

from flask import Flask, jsonify

from config import get_config

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)


def create_app(config_name: str = "development") -> Flask:
    """
    Create and configure the Flask application.

    Args:
        config_name: One of development, production, testing.

    Returns:
        Configured Flask app with blueprints registered.
    """
    app = Flask(
        __name__,
        template_folder="templates",
        static_folder="static",
    )

    app.config.from_object(get_config(config_name))

    # Register route blueprints (import here to avoid circular imports)
    from app.routes.disease import disease_bp
    from app.routes.recommendation import recommendation_bp
    from app.routes.assistant import assistant_bp

    app.register_blueprint(disease_bp)
    app.register_blueprint(recommendation_bp)
    app.register_blueprint(assistant_bp)

    @app.errorhandler(404)
    def not_found(_error):
        return jsonify({"error": "Resource not found"}), 404

    @app.errorhandler(500)
    def server_error(error):
        logging.getLogger(__name__).exception("Server error: %s", error)
        return jsonify({"error": "Internal server error"}), 500

    return app
