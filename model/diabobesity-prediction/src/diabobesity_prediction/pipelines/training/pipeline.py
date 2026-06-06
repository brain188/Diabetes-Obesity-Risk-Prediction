from kedro.pipeline import Pipeline, node

from .nodes import (
    evaluate_final_model,
    save_model_artifacts,
    select_best_model,
    train_candidates,
)


def create_training_pipeline(**kwargs) -> Pipeline:
    """
    Return the fully wired Training pipeline.

    """
    return Pipeline(
        [
            node(
                func    = train_candidates,
                inputs  = [
                    "X_train",
                    "y_train_final",
                    "X_val",
                    "y_val_final",
                    "params:training.mlflow_experiment_name",
                    "params:training.cv_folds",
                    "params:training.random_state",
                ],
                outputs = "candidate_results",
                name    = "train_candidates_node",
            ),
            node(
                func    = select_best_model,
                inputs  = "candidate_results",
                outputs = [
                    "best_model",
                    "best_model_name",
                    "best_val_metrics",
                ],
                name    = "select_best_model_node",
            ),
            node(
                func    = evaluate_final_model,
                inputs  = [
                    "best_model",
                    "best_model_name",
                    "X_val",
                    "y_val_final",
                    "X_test",
                    "y_test_final",
                    "params:training.mlflow_experiment_name",
                ],
                outputs = "evaluation_report",
                name    = "evaluate_final_model_node",
            ),
            node(
                func    = save_model_artifacts,
                inputs  = [
                    "best_model",
                    "best_model_name",
                    "evaluation_report",
                    "scaler",
                ],
                outputs = [
                    "trained_model",
                    "model_metadata",
                ],
                name    = "save_model_artifacts_node",
            ),
        ]
    )