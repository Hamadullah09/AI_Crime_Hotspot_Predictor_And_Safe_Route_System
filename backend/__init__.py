from pathlib import Path

from flask import Flask, jsonify

from .routes import api_bp


def create_app():
    """Create and configure the Flask application."""
    project_root = Path(__file__).resolve().parents[1]
    template_dir = project_root / "frontend" / "templates"
    static_dir = project_root / "frontend" / "static"

    app = Flask(
        __name__,
        template_folder=str(template_dir),
        static_folder=str(static_dir),
        static_url_path="/static",
    )
    app.config["JSON_SORT_KEYS"] = False
    app.register_blueprint(api_bp)

    @app.errorhandler(404)
    def not_found(_error):
        return jsonify({"error": "Route not found."}), 404

    @app.errorhandler(500)
    def internal_error(_error):
        return jsonify({"error": "Internal server error."}), 500

    return app
