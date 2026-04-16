"""
GET /analytics  — aggregate statistics for the dashboard.
"""

import logging
from flask import jsonify
from flask import Blueprint
from database.db import get_analytics

logger = logging.getLogger(__name__)
analytics_bp = Blueprint("analytics", __name__)


@analytics_bp.route("/analytics", methods=["GET"])
def analytics():
    """
    Returns:
        {
          "total": 120,
          "by_label": {
            "Safe":     {"count": 80, "avg_confidence": 0.92},
            "Phishing": {"count": 40, "avg_confidence": 0.88}
          },
          "phishing_rate": 0.333
        }
    """
    try:
        data = get_analytics()
    except Exception as exc:
        logger.exception("Analytics query failed.")
        return jsonify({"error": "Could not retrieve analytics."}), 500

    total = data.get("total", 0)
    phishing_count = data.get("by_label", {}).get("Phishing", {}).get("count", 0)
    phishing_rate  = round(phishing_count / total, 4) if total else 0.0

    data["phishing_rate"] = phishing_rate
    return jsonify(data), 200
