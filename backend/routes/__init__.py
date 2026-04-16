"""
Routes Package
"""
from .predict import predict_bp
from .history import history_bp
from .analytics import analytics_bp

__all__ = ["predict_bp", "history_bp", "analytics_bp"]
