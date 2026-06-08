"""Project pipelines."""

from kedro.pipeline import Pipeline

from .pipelines.data_processing import create_data_processing_pipeline as dp
from .pipelines.evaluation import create_evaluation_pipeline as ev
from .pipelines.feature_engineering import create_feature_engineering_pipeline as fe
from .pipelines.prediction import create_prediction_pipeline as pr
from .pipelines.training import create_training_pipeline as tr


def register_pipelines() -> dict[str, Pipeline]:
    """Register the project's pipelines.

    """
    data_processing_pipeline = dp()
    feature_engineering_pipeline = fe()
    training_pipeline = tr()
    evaluation_pipeline = ev()
    prediction_pipeline = pr()

    return {
        "__default__": ( data_processing_pipeline
                        + feature_engineering_pipeline
                        + training_pipeline
                        + evaluation_pipeline
        ),
        "data_processing": data_processing_pipeline,
        "feature_engineering": feature_engineering_pipeline,
        "training": training_pipeline,
        "evaluation": evaluation_pipeline,
        "prediction": prediction_pipeline,
    }
