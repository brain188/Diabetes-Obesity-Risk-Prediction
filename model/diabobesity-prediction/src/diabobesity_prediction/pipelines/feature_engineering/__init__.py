"""
feature_engineering
===================
Kedro pipeline package for the Feature Engineering stage.

Exposes ``create_feature_engineering_pipeline`` so the Kedro framework can discover and
register this pipeline through ``pipeline_registry.py``.
"""

from .pipeline import create_feature_engineering_pipeline

__all__ = ["create_feature_engineering_pipeline"]