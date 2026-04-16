"""
Database layer — MongoDB primary, SQLite fallback.
─────────────────────────────────────────────────
All external call-sites should import from this module only.
Connection parameters are read from environment variables:
    MONGO_URI      (default: mongodb://localhost:27017)
    MONGO_DB_NAME  (default: phishing_detector)
"""

import os
import json
import logging
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────
#  MongoDB (primary)
# ─────────────────────────────────────────────
try:
    from pymongo import MongoClient, DESCENDING
    from pymongo.errors import ConnectionFailure

    _mongo_uri = os.getenv("MONGO_URI", "mongodb://localhost:27017")
    _mongo_db  = os.getenv("MONGO_DB_NAME", "phishing_detector")
    _client    = MongoClient(_mongo_uri, serverSelectionTimeoutMS=2_000)
    _client.admin.command("ping")           # will raise if not reachable
    _db        = _client[_mongo_db]
    _col       = _db["predictions"]
    USE_MONGO  = True
    logger.info("✅ Connected to MongoDB at %s", _mongo_uri)

except Exception as exc:
    USE_MONGO = False
    logger.warning("⚠️  MongoDB unavailable (%s) — falling back to SQLite.", exc)


# ─────────────────────────────────────────────
#  SQLite (fallback)
# ─────────────────────────────────────────────
_SQLITE_PATH = Path(__file__).parent / "phishing.db"


def _get_sqlite_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(str(_SQLITE_PATH))
    conn.row_factory = sqlite3.Row
    return conn


def _ensure_sqlite_schema():
    with _get_sqlite_conn() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS predictions (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                url         TEXT    NOT NULL,
                prediction  TEXT    NOT NULL,
                confidence  REAL    NOT NULL,
                features    TEXT,
                timestamp   TEXT    NOT NULL
            )
        """)
        conn.commit()


if not USE_MONGO:
    _ensure_sqlite_schema()


# ─────────────────────────────────────────────
#  Public API
# ─────────────────────────────────────────────

def save_prediction(url: str, prediction: str,
                    confidence: float, features: Optional[dict] = None) -> str:
    """
    Persist a prediction record and return its string ID.

    Parameters
    ----------
    url        : The submitted URL.
    prediction : 'Safe' or 'Phishing'.
    confidence : Float in [0, 1].
    features   : Optional dict of extracted features.
    """
    timestamp = datetime.now(timezone.utc).isoformat()

    if USE_MONGO:
        doc = {
            "url":        url,
            "prediction": prediction,
            "confidence": confidence,
            "features":   features or {},
            "timestamp":  timestamp,
        }
        result = _col.insert_one(doc)
        return str(result.inserted_id)

    # SQLite path
    with _get_sqlite_conn() as conn:
        cur = conn.execute(
            """INSERT INTO predictions (url, prediction, confidence, features, timestamp)
               VALUES (?, ?, ?, ?, ?)""",
            (url, prediction, confidence,
             json.dumps(features or {}), timestamp),
        )
        conn.commit()
        return str(cur.lastrowid)


def get_history(limit: int = 100) -> list[dict]:
    """
    Return the most-recent *limit* prediction records, newest first.
    """
    if USE_MONGO:
        docs = list(
            _col.find({}, {"_id": 0})
                .sort("timestamp", DESCENDING)
                .limit(limit)
        )
        return docs

    # SQLite path
    with _get_sqlite_conn() as conn:
        rows = conn.execute(
            """SELECT id, url, prediction, confidence, features, timestamp
               FROM predictions
               ORDER BY timestamp DESC
               LIMIT ?""",
            (limit,),
        ).fetchall()

    result = []
    for row in rows:
        d = dict(row)
        try:
            d["features"] = json.loads(d.get("features") or "{}")
        except (ValueError, TypeError):
            d["features"] = {}
        result.append(d)
    return result


def clear_history() -> int:
    """
    Delete all stored prediction records.
    Returns the number of deleted documents/rows.
    """
    if USE_MONGO:
        result = _col.delete_many({})
        return result.deleted_count

    with _get_sqlite_conn() as conn:
        cur = conn.execute("DELETE FROM predictions")
        conn.commit()
        return cur.rowcount


def get_analytics() -> dict:
    """
    Return aggregate statistics for the dashboard.
    """
    if USE_MONGO:
        pipeline = [
            {"$group": {
                "_id":           "$prediction",
                "count":         {"$sum": 1},
                "avg_confidence":{"$avg": "$confidence"},
            }},
        ]
        raw = list(_col.aggregate(pipeline))
        stats = {doc["_id"]: {"count": doc["count"],
                              "avg_confidence": round(doc["avg_confidence"], 4)}
                 for doc in raw}
        total = sum(v["count"] for v in stats.values())
        return {"total": total, "by_label": stats}

    # SQLite path
    with _get_sqlite_conn() as conn:
        rows = conn.execute(
            """SELECT prediction,
                      COUNT(*)       AS count,
                      AVG(confidence) AS avg_confidence
               FROM predictions
               GROUP BY prediction"""
        ).fetchall()
        total_row = conn.execute("SELECT COUNT(*) FROM predictions").fetchone()

    stats = {r["prediction"]: {"count": r["count"],
                                "avg_confidence": round(r["avg_confidence"] or 0, 4)}
             for r in rows}
    return {"total": total_row[0], "by_label": stats}
