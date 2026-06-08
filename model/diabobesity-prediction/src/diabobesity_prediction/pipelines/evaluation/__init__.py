"""
evaluation
==========
Kedro pipeline package for the Evaluation stage.

Exposes ``create_evaluation_pipeline`` so the Kedro framework can discover and
register this pipeline through ``pipeline_registry.py``.
"""

from .pipeline import create_evaluation_pipeline

__all__ = ["create_evaluation_pipeline"]
