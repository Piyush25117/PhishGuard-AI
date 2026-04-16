"""
POST /predict
─────────────
Accepts a JSON body  { "url": "https://example.com" }
Extracts features, runs the Random Forest model, stores the result,
and returns the classification + confidence score.
"""

import os
import re
import pickle
import logging
import tldextract
from pathlib import Path
from flask import Blueprint, request, jsonify

from feature_extraction import extract_features, features_to_vector
from database.db import save_prediction

logger = logging.getLogger(__name__)

predict_bp = Blueprint("predict", __name__)

# ── Load model once at import time ──────────────────────────────────────────
_MODEL_PATH = Path(__file__).parent.parent / "model.pkl"
_model_meta: dict | None = None


def _load_model():
    global _model_meta
    if _model_meta is None:
        if not _MODEL_PATH.exists():
            raise FileNotFoundError(
                f"model.pkl not found at {_MODEL_PATH}. "
                "Run `python backend/train_model.py` first."
            )
        with open(_MODEL_PATH, "rb") as fh:
            _model_meta = pickle.load(fh)
        logger.info("✅ Model loaded from %s", _MODEL_PATH)
    return _model_meta


# ── Basic URL validation ─────────────────────────────────────────────────────
_URL_RE = re.compile(
    r"^(https?://)?"
    r"([\w\-]+\.)+[\w\-]{2,}"
    r"([/?#].*)?$",
    re.IGNORECASE,
)

_MAX_URL_LEN = 2_048


def _validate_url(url: str):
    if not url or not isinstance(url, str):
        raise ValueError("URL must be a non-empty string.")
    url = url.strip()
    if len(url) > _MAX_URL_LEN:
        raise ValueError(f"URL exceeds maximum length ({_MAX_URL_LEN} chars).")
    if not url.startswith(("http://", "https://")):
        url = "https://" + url
    if not _URL_RE.match(url):
        raise ValueError("URL format is invalid.")
    for bad in ["<script", "javascript:", "data:", "vbscript:"]:
        if bad.lower() in url.lower():
            raise ValueError("URL contains disallowed content.")
    return url


# ── Route handler ────────────────────────────────────────────────────────────
@predict_bp.route("/predict", methods=["POST"])
def predict():

    body = request.get_json(silent=True) or {}
    raw_url = body.get("url", "")

    # ── Validate input ───────────────────────────────────────────────────────
    try:
        url = _validate_url(raw_url)
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400

    # ── Feature extraction ───────────────────────────────────────────────────
    try:
        features = extract_features(url)
    except ValueError as exc:
        return jsonify({"error": f"Feature extraction failed: {exc}"}), 400
    except Exception:
        logger.exception("Unexpected error during feature extraction.")
        return jsonify({"error": "Internal server error during feature extraction."}), 500

    # ── Trusted Domain Override (FIXED ✅) ────────────────────────────────────
    trusted_domains = [
        "google", "youtube", "amazon", "github", "facebook",
        "microsoft", "apple", "linkedin", "wikipedia"
    ]

    extracted = tldextract.extract(url)
    if extracted.domain.lower() in trusted_domains:
        prediction = "Safe"
        confidence = 0.95

        # ✅ SAVE TO DATABASE (FIX)
        try:
            record_id = save_prediction(url, prediction, confidence, features)
        except Exception as exc:
            logger.warning("Database write failed (non-fatal): %s", exc)
            record_id = None

        return jsonify({
            "id": record_id,
            "url": url,
            "prediction": prediction,
            "confidence": confidence,
            "features": features
        }), 200

    # ── ML prediction ────────────────────────────────────────────────────────
    try:
        meta      = _load_model()
        pipeline  = meta["pipeline"]
        labels    = meta["labels"]

        feature_vector = [features_to_vector(features)]
        pred_idx       = int(pipeline.predict(feature_vector)[0])
        proba          = pipeline.predict_proba(feature_vector)[0]
        confidence     = float(proba[pred_idx])
        prediction     = labels[pred_idx]

    except FileNotFoundError as exc:
        return jsonify({"error": str(exc)}), 503
    except Exception:
        logger.exception("Prediction failed.")
        return jsonify({"error": "ML prediction failed. Please try again."}), 500

    # ── Persist result ───────────────────────────────────────────────────────
    try:
        record_id = save_prediction(url, prediction, confidence, features)
    except Exception as exc:
        logger.warning("Database write failed (non-fatal): %s", exc)
        record_id = None

    return jsonify({
        "id": record_id,
        "url": url,
        "prediction": prediction,
        "confidence": round(confidence, 4),
        "features": features,
    }), 200