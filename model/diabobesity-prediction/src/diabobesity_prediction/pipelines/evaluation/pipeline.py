from kedro.pipeline import Pipeline, node

from .nodes import (
    build_evaluation_report,
    compute_lime_explanation,
    compute_shap_values,
    compute_test_metrics,
    plot_confusion_matrix,
    plot_feature_importance,
    plot_roc_curves,
    save_shap_explainer,
)


def create_evaluation_pipeline(**kwargs) -> Pipeline:
    """
    Return the fully wired Evaluation pipeline.

    """
    return Pipeline(
        [
            node(
                func    = compute_test_metrics,
                inputs  = [
                    "trained_model",
                    "X_test",
                    "y_test_final",
                ],
                outputs = "test_metrics_output",
                name    = "compute_test_metrics_node",
            ),
            node(
                func    = plot_confusion_matrix,
                inputs  = [
                    "trained_model",
                    "X_test",
                    "y_test_final",
                ],
                outputs = "confusion_matrix_png",
                name    = "plot_confusion_matrix_node",
            ),
            node(
                func    = plot_roc_curves,
                inputs  = [
                    "trained_model",
                    "X_test",
                    "y_test_final",
                ],
                outputs = "roc_curves_png",
                name    = "plot_roc_curves_node",
            ),
            node(
                func    = compute_shap_values,
                inputs  = [
                    "trained_model",
                    "X_train",
                    "X_test",
                ],
                outputs = [
                    "shap_bar_png",
                    "shap_beeswarm_png",
                ],
                name    = "compute_shap_values_node",
            ),
            node(
                func    = save_shap_explainer,
                inputs  = [
                    "trained_model",
                    "X_train",
                ],
                outputs = "shap_explainer",
                name    = "save_shap_explainer_node",
            ),
            node(
                func=compute_lime_explanation,
                inputs=[
                    "trained_model",
                    "X_train",
                    "X_test",
                    "model_metadata",
                ],
                outputs="lime_explanation_png",
                name="compute_lime_explanation_node",
            ),

            node(
                func=plot_feature_importance,
                inputs=[
                    "trained_model",
                    "model_metadata",
                ],
                outputs="feature_importance_png",
                name="plot_feature_importance_node",
            ),
            node(
                func    = build_evaluation_report,
                inputs  = [
                    "test_metrics_output",
                    "model_metadata",
                ],
                outputs = "full_evaluation_report",
                name    = "build_evaluation_report_node",
            ),
        ]
    )
