"""
GET  /history          → recent predictions (newest first)
DELETE /history        → wipe all stored predictions
"""

import logging
from flask import Blueprint, request, jsonify
from database.db import get_history, clear_history

logger = logging.getLogger(__name__)
history_bp = Blueprint("history", __name__)


@history_bp.route("/history", methods=["GET"])
def history():
    """
    Query params:
        limit (int, default=50, max=500)

    Response: list of prediction objects, newest first.
    """
    try:
        limit = int(request.args.get("limit", 50))
        limit = max(1, min(limit, 500))     # clamp to [1, 500]
    except (ValueError, TypeError):
        limit = 50

    try:
        records = get_history(limit)
    except Exception as exc:
        logger.exception("Failed to retrieve history.")
        return jsonify({"error": "Could not retrieve history from database."}), 500

    return jsonify({"count": len(records), "records": records}), 200


@history_bp.route("/history", methods=["DELETE"])
def delete_history():
    """
    Clear all prediction history.
    Response: { "deleted": <count> }
    """
    try:
        deleted = clear_history()
    except Exception as exc:
        logger.exception("Failed to clear history.")
        return jsonify({"error": "Could not clear history."}), 500

    return jsonify({"deleted": deleted, "message": "History cleared successfully."}), 200
