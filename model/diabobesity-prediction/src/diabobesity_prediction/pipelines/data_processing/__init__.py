"""
data_processing
===============
Kedro pipeline package for the Data Processing stage.

Exposes ``create_data_processing_pipeline`` so the Kedro framework can discover and register
this pipeline through ``pipeline_registry.py``.
"""

from .pipeline import create_data_processing_pipeline

__all__ = ["create_data_processing_pipeline"]