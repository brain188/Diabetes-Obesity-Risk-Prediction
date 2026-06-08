"""
prediction
==========
Kedro pipeline package for the Prediction (inference) stage.

Exposes ``create_prediction_pipeline`` so the Kedro framework can discover and
register this pipeline through ``pipeline_registry.py``.
"""

from .pipeline import create_prediction_pipeline

__all__ = ["create_prediction_pipeline"]