"""
Model Training Script
─────────────────────
Trains a Random Forest classifier on a synthetic (but realistic)
phishing-vs-safe dataset, then persists the model as model.pkl.

Run once:
    python backend/train_model.py

The script also prints a classification report so you can evaluate
the model before deploying it.
"""

import os
import pickle
import logging
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import classification_report, confusion_matrix
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline

logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s  %(levelname)s  %(message)s")
logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────
#  Synthetic Dataset Generation
#  (Replace with a real labelled CSV in production,
#   e.g. the UCI Phishing Dataset)
# ─────────────────────────────────────────────

FEATURE_NAMES = [
    "url_length",
    "has_ip_address",
    "has_at_symbol",
    "has_double_slash_redirect",
    "has_hyphen_in_domain",
    "count_dots",
    "uses_https",
    "domain_length",
    "count_subdomains",
    "url_path_length",
    "has_suspicious_tld",
    "count_special_chars",
    "has_port_in_url",
    "domain_age_days",
    "ssl_valid",
    "page_rank_mock",
]

N_SAFE     = 3_000
N_PHISHING = 3_000
rng = np.random.default_rng(42)


def _gen_safe(n: int) -> np.ndarray:
    """Simulate feature vectors for legitimate websites."""
    return np.column_stack([
        rng.integers(20,  80,  n),          # url_length
        rng.integers(0,   2,   n, endpoint=False) * 0,  # has_ip_address  ← rarely 1
        np.zeros(n, dtype=int),             # has_at_symbol
        np.zeros(n, dtype=int),             # has_double_slash_redirect
        rng.integers(0, 2, n),              # has_hyphen_in_domain
        rng.integers(1, 4, n),              # count_dots
        np.ones(n, dtype=int),              # uses_https
        rng.integers(4, 15, n),             # domain_length
        rng.integers(0, 2, n),              # count_subdomains
        rng.integers(1, 30, n),             # url_path_length
        np.zeros(n, dtype=int),             # has_suspicious_tld
        rng.integers(0, 5, n),              # count_special_chars
        np.zeros(n, dtype=int),             # has_port_in_url
        rng.integers(365, 5000, n),         # domain_age_days
        np.ones(n, dtype=int),              # ssl_valid
        rng.random(n).round(1),             # page_rank_mock
    ]).astype(float)


def _gen_phishing(n: int) -> np.ndarray:
    """Simulate feature vectors for phishing/scam websites."""
    return np.column_stack([
        rng.integers(60, 200, n),           # url_length (long)
        rng.integers(0, 2, n),              # has_ip_address
        rng.integers(0, 2, n),              # has_at_symbol
        rng.integers(0, 2, n),              # has_double_slash_redirect
        rng.integers(1, 2, n),              # has_hyphen_in_domain
        rng.integers(3, 8, n),              # count_dots
        rng.integers(0, 2, n),              # uses_https
        rng.integers(2, 20, n),             # domain_length
        rng.integers(2, 5, n),              # count_subdomains
        rng.integers(20, 100, n),           # url_path_length
        rng.integers(0, 2, n),              # has_suspicious_tld
        rng.integers(3, 15, n),             # count_special_chars
        rng.integers(0, 2, n),              # has_port_in_url
        rng.integers(0, 30, n),             # domain_age_days (very new)
        np.zeros(n, dtype=int),             # ssl_valid (no cert)
        np.zeros(n, dtype=float),           # page_rank_mock
    ]).astype(float)


def build_dataset():
    safe     = _gen_safe(N_SAFE)
    phishing = _gen_phishing(N_PHISHING)
    X = np.vstack([safe, phishing])
    y = np.array([0] * N_SAFE + [1] * N_PHISHING)   # 0=safe, 1=phishing
    return X, y


# ─────────────────────────────────────────────
#  Training
# ─────────────────────────────────────────────

def train():
    logger.info("Building synthetic dataset …")
    X, y = build_dataset()

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    # Pipeline: scaler + Random Forest
    pipeline = Pipeline([
        ("scaler", StandardScaler()),
        ("clf", RandomForestClassifier(
            n_estimators=200,
            max_depth=15,
            min_samples_split=5,
            class_weight="balanced",
            random_state=42,
            n_jobs=-1,
        )),
    ])

    logger.info("Training Random Forest …")
    pipeline.fit(X_train, y_train)

    # Cross-validation
    cv_scores = cross_val_score(pipeline, X_train, y_train, cv=5, scoring="f1")
    logger.info("5-fold CV F1: %.4f ± %.4f", cv_scores.mean(), cv_scores.std())

    # Held-out evaluation
    y_pred = pipeline.predict(X_test)
    logger.info("\n%s", classification_report(y_test, y_pred,
                                              target_names=["Safe", "Phishing"]))
    logger.info("Confusion matrix:\n%s", confusion_matrix(y_test, y_pred))

    # Persist
    model_path = os.path.join(os.path.dirname(__file__), "model.pkl")
    meta = {
        "pipeline":      pipeline,
        "feature_names": FEATURE_NAMES,
        "labels":        {0: "Safe", 1: "Phishing"},
        "trained_at":    __import__("datetime").datetime.utcnow().isoformat(),
    }
    with open(model_path, "wb") as fh:
        pickle.dump(meta, fh)

    logger.info("Model saved → %s", model_path)
    return pipeline


if __name__ == "__main__":
    train()
