"""
training
========
Kedro pipeline package for the Training stage.

Exposes ``create_training_pipeline`` so the Kedro framework can discover and
register this pipeline through ``pipeline_registry.py``.
"""

from .pipeline import create_training_pipeline

__all__ = ["create_training_pipeline"]
