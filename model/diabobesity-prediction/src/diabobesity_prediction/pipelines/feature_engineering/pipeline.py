from kedro.pipeline import Pipeline, node
 
from .nodes import (
    apply_smote,
    final_feature_check,
    scale_features,
    separate_features_target,
    split_train_validation,
)


def create_feature_engineering_pipeline(**kwargs) -> Pipeline:
    """
    Return the fully wired Feature Engineering pipeline.
 
    """
    return Pipeline(
        [
            node(
                func    = split_train_validation,
                inputs  = [
                    "diabetes_train_cleaned",
                    "params:feature_engineering.val_size",
                    "params:feature_engineering.random_state",
                ],
                outputs = [
                    "train_split",
                    "val_split",
                ],
                name    = "split_train_validation_node",
            ),
            node(
                func    = separate_features_target,
                inputs  = [
                    "train_split",
                    "val_split",
                    "diabetes_test_cleaned",
                    "params:feature_engineering.target_col",
                    "params:feature_engineering.drop_cols",
                ],
                outputs = [
                    "X_train_raw",
                    "y_train_raw",
                    "X_val_raw",
                    "y_val",
                    "X_test_raw",
                    "y_test",
                ],
                name    = "separate_features_target_node",
            ),
            node(
                func    = scale_features,
                inputs  = [
                    "X_train_raw",
                    "X_val_raw",
                    "X_test_raw",
                ],
                outputs = [
                    "X_train_scaled",
                    "X_val_scaled",
                    "X_test_scaled",
                    "scaler",
                ],
                name    = "scale_features_node",
            ),
            node(
                func    = apply_smote,
                inputs  = [
                    "X_train_scaled",
                    "y_train_raw",
                    "params:feature_engineering.smote_random_state",
                    "params:feature_engineering.smote_k_neighbors",
                ],
                outputs = [
                    "X_train_resampled",
                    "y_train_resampled",
                ],
                name    = "apply_smote_node",
            ),
            node(
                func    = final_feature_check,
                inputs  = [
                    "X_train_resampled",
                    "y_train_resampled",
                    "X_val_scaled",
                    "y_val",
                    "X_test_scaled",
                    "y_test",
                ],
                outputs = [
                    "X_train",
                    "y_train_final",
                    "X_val",
                    "y_val_final",
                    "X_test",
                    "y_test_final",
                ],
                name    = "final_feature_check_node",
            ),
        ]
    )