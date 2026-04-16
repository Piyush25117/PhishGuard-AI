"""
Flask Application Entry Point
──────────────────────────────
Start the server:
    python backend/app.py

Or via gunicorn (production):
    gunicorn -w 4 -b 0.0.0.0:5000 "app:create_app()"
"""

import os
import sys
import logging
from flask import Flask, jsonify
from flask_cors import CORS

# ── Logging ──────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(name)s — %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)


def create_app() -> Flask:
    app = Flask(__name__)

    # ── CORS — allow the React dev-server (port 3000) and any other origin ──
    CORS(app, resources={r"/api/*": {"origins": "*"}})

    # ── Register blueprints (all routes live under /api) ────────────────────
    from routes.predict   import predict_bp
    from routes.history   import history_bp
    from routes.analytics import analytics_bp

    app.register_blueprint(predict_bp,   url_prefix="/api")
    app.register_blueprint(history_bp,   url_prefix="/api")
    app.register_blueprint(analytics_bp, url_prefix="/api")

    # ── Health check ─────────────────────────────────────────────────────────
    @app.route("/api/health", methods=["GET"])
    def health():
        return jsonify({"status": "ok", "service": "Phishing Detector API"}), 200

    # ── 404 / 405 handlers ───────────────────────────────────────────────────
    @app.errorhandler(404)
    def not_found(_):
        return jsonify({"error": "Endpoint not found."}), 404

    @app.errorhandler(405)
    def method_not_allowed(_):
        return jsonify({"error": "Method not allowed."}), 405

    @app.errorhandler(500)
    def server_error(_):
        return jsonify({"error": "Internal server error."}), 500

    logger.info("Flask app created — blueprints: predict, history, analytics")
    return app


# ── Dev runner ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    port  = int(os.getenv("PORT", 5000))
    debug = os.getenv("FLASK_DEBUG", "1") == "1"
    app   = create_app()
    logger.info("🚀 Starting dev server on http://0.0.0.0:%d", port)
    app.run(host="0.0.0.0", port=port, debug=debug)
