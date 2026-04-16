"""
Feature Extraction Module
Extracts relevant features from URLs for ML-based phishing detection.
"""

import re
import ssl
import socket
import whois
import requests
import tldextract
from urllib.parse import urlparse
from datetime import datetime, timezone
import logging

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────

def _safe_get(url: str, timeout: int = 5):
    try:
        return requests.get(url, timeout=timeout, allow_redirects=True,
                            headers={"User-Agent": "Mozilla/5.0"})
    except Exception:
        return None


# ─────────────────────────────────────────────
# Feature Functions
# ─────────────────────────────────────────────

def get_url_length(url: str) -> int:
    return len(url)


def has_ip_address(url: str) -> int:
    ip_pattern = re.compile(r"((\d{1,3}\.){3}\d{1,3})")
    hostname = urlparse(url).netloc
    return 1 if ip_pattern.search(hostname) else 0


def has_at_symbol(url: str) -> int:
    return 1 if "@" in url else 0


def has_double_slash_redirect(url: str) -> int:
    stripped = url[7:] if url.startswith("http") else url
    return 1 if "//" in stripped else 0


def has_hyphen_in_domain(url: str) -> int:
    domain = urlparse(url).netloc
    return 1 if "-" in domain else 0


def count_dots(url: str) -> int:
    return url.count(".")


def uses_https(url: str) -> int:
    return 1 if urlparse(url).scheme.lower() == "https" else 0


def domain_length(url: str) -> int:
    extracted = tldextract.extract(url)
    return len(extracted.domain)


def count_subdomains(url: str) -> int:
    extracted = tldextract.extract(url)
    return len(extracted.subdomain.split(".")) if extracted.subdomain else 0


def url_path_length(url: str) -> int:
    return len(urlparse(url).path)


def has_suspicious_tld(url: str) -> int:
    suspicious_tlds = {
        "tk", "ml", "ga", "cf", "gq",
        "xyz", "top", "click", "link",
        "club", "online", "site", "website",
        "loan", "work", "date", "faith",
        "stream", "download", "racing",
    }
    extracted = tldextract.extract(url)
    return 1 if extracted.suffix.lower() in suspicious_tlds else 0


def count_special_chars(url: str) -> int:
    chars = ["@", "-", "=", "&", "?", "%", "~"]
    return sum(url.count(c) for c in chars)


def has_port_in_url(url: str) -> int:
    parsed = urlparse(url)
    return 1 if parsed.port and parsed.port not in (80, 443) else 0


def domain_age_days(url: str) -> int:
    try:
        extracted = tldextract.extract(url)
        domain = f"{extracted.domain}.{extracted.suffix}"
        w = whois.whois(domain)
        creation = w.creation_date

        if isinstance(creation, list):
            creation = creation[0]

        if creation is None:
            return -1

        now = datetime.now(timezone.utc)

        if creation.tzinfo is None:
            creation = creation.replace(tzinfo=timezone.utc)

        age = (now - creation).days
        return max(age, 0)

    except Exception:
        return -1


def ssl_valid(url: str) -> int:
    try:
        parsed = urlparse(url)
        hostname = parsed.hostname

        if not hostname:
            return 0

        ctx = ssl.create_default_context()

        with ctx.wrap_socket(
            socket.create_connection((hostname, 443), timeout=5),
            server_hostname=hostname,
        ):
            return 1

    except Exception:
        return 0


def page_rank_mock(url: str) -> float:
    known_safe = {
        "google", "youtube", "facebook", "amazon",
        "twitter", "microsoft", "apple", "github",
        "linkedin", "wikipedia", "instagram",
    }

    extracted = tldextract.extract(url)
    return 1.0 if extracted.domain.lower() in known_safe else 0.2


# ─────────────────────────────────────────────
# Feature Pipeline
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


def extract_features(url: str) -> dict:
    parsed = urlparse(url)

    if not parsed.scheme or not parsed.netloc:
        raise ValueError(f"Invalid URL: {url}")

    features = {
        "url_length":               get_url_length(url),
        "has_ip_address":           has_ip_address(url),
        "has_at_symbol":            has_at_symbol(url),
        "has_double_slash_redirect":has_double_slash_redirect(url),
        "has_hyphen_in_domain":     has_hyphen_in_domain(url),
        "count_dots":               count_dots(url),
        "uses_https":               uses_https(url),
        "domain_length":            domain_length(url),
        "count_subdomains":         count_subdomains(url),
        "url_path_length":          url_path_length(url),
        "has_suspicious_tld":       has_suspicious_tld(url),
        "count_special_chars":      count_special_chars(url),
        "has_port_in_url":          has_port_in_url(url),
        "domain_age_days":          domain_age_days(url),
        "ssl_valid":                ssl_valid(url),
        "page_rank_mock":           page_rank_mock(url),
    }

    # ✅ FIX: neutral fallback instead of extreme
    if features["domain_age_days"] == -1:
        features["domain_age_days"] = 180

    logger.debug("Features for %s: %s", url, features)
    return features


def features_to_vector(features: dict) -> list:
    return [features[name] for name in FEATURE_NAMES]