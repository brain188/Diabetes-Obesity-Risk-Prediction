from kedro.pipeline import Pipeline, node

from .nodes import (
    build_prediction_response,
    classify_risk_band,
    explain_prediction,
    preprocess_patient_input,
    run_prediction,
    validate_patient_input,
    explain_prediction_lime,
    get_feature_importance,
)


def create_prediction_pipeline(**kwargs) -> Pipeline:
    """
    Return the fully wired Prediction pipeline.

    """
    return Pipeline(
        [
            node(
                func    = validate_patient_input,
                inputs  = [
                    "raw_patient",
                    "params:prediction.feature_names",
                ],
                outputs = "validated_patient",
                name    = "validate_patient_input_node",
            ),
            node(
                func    = preprocess_patient_input,
                inputs  = [
                    "validated_patient",
                    "scaler",
                    "model_metadata",
                ],
                outputs = "patient_features",
                name    = "preprocess_patient_input_node",
            ),
            node(
                func    = run_prediction,
                inputs  = [
                    "trained_model",
                    "patient_features",
                ],
                outputs = "prediction_output",
                name    = "run_prediction_node",
            ),
            node(
                func    = classify_risk_band,
                inputs  = [
                    "prediction_output",
                    "model_metadata",
                ],
                outputs = "risk_band_output",
                name    = "classify_risk_band_node",
            ),
            node(
                func    = explain_prediction,
                inputs  = [
                    "shap_explainer",
                    "patient_features",
                    "model_metadata",
                ],
                outputs = "explanation_output",
                name    = "explain_prediction_node",
            ),
            node(
                func    = explain_prediction_lime,
                inputs  = [
                    "trained_model",
                    "patient_features",
                    "X_train",
                    "model_metadata",
                ],
                outputs = "lime_explanation_output",
                name    = "explain_prediction_lime_node",
            ),

            node(
                func    = get_feature_importance,
                inputs  = [
                    "trained_model",
                    "model_metadata",
                ],
                outputs = "feature_importance_output",
                name    = "get_feature_importance_node",
            ),
            node(
                func    = build_prediction_response,
                inputs  = [
                    "validated_patient",
                    "prediction_output",
                    "risk_band_output",
                    "explanation_output",
                    "lime_explanation_output",
                    "feature_importance_output",
                ],
                outputs = "prediction_response",
                name    = "build_prediction_response_node",
            ),
        ]
    )
