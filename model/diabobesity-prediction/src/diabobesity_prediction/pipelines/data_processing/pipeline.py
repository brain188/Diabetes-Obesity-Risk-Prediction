from kedro.pipeline import Pipeline, node

from .nodes import (
    convert_age,
    encode_bmi_category,
    encode_booleans,
    encode_residence,
    encode_sex,
    encode_target,
    final_quality_check,
    load_and_inspect,
    select_columns,
)


def create_data_processing_pipeline(**kwargs) -> Pipeline:
    """
    Return the fully wired data processing pipeline

    """
    return Pipeline(
        [
            node(
                func = load_and_inspect,
                inputs = ["diabetes_train_raw", "diabetes_test_raw"],
                outputs = ["diabetes_train_inspected", "diabetes_test_inspected"],
                name = "load_and_inspect_node"
            ),
            node(
                func = select_columns,
                inputs = ["diabetes_train_inspected", "diabetes_test_inspected", "params:data_processing.columns_to_keep"],
                outputs = ["diabetes_train_selected", "diabetes_test_selected"],
                name = "select_columns_node"
            ),
            node(
                func = encode_target,
                inputs = ["diabetes_train_selected", "diabetes_test_selected", "params:data_processing.target_map"],
                outputs = ["diabetes_train_target_encoded", "diabetes_test_target_encoded"],
                name = "encode_target_node"
            ),
            node(
                func = encode_booleans,
                inputs = ["diabetes_train_target_encoded", "diabetes_test_target_encoded", "params:data_processing.boolean_columns"],
                outputs = ["diabetes_train_booleans_encoded", "diabetes_test_booleans_encoded"],
                name = "encode_booleans_node"
            ),
            node(
                func = encode_bmi_category,
                inputs = ["diabetes_train_booleans_encoded", "diabetes_test_booleans_encoded", "params:data_processing.bmi_map"],
                outputs = ["diabetes_train_bmi_encoded", "diabetes_test_bmi_encoded"],
                name = "encode_bmi_category_node"
            ),
            node(
                func = encode_sex,
                inputs = ["diabetes_train_bmi_encoded", "diabetes_test_bmi_encoded", "params:data_processing.sex_map"],
                outputs = ["diabetes_train_sex_encoded", "diabetes_test_sex_encoded"],
                name = "encode_sex_node"
            ),
            node(
                func = encode_residence,
                inputs = ["diabetes_train_sex_encoded", "diabetes_test_sex_encoded", "params:data_processing.residence_map"],
                outputs = ["diabetes_train_residence_encoded", "diabetes_test_residence_encoded"],
                name = "encode_residence_map"
            ),
            node(
                func = convert_age,
                inputs = ["diabetes_train_residence_encoded", "diabetes_test_residence_encoded"],
                outputs = ["diabetes_train_age_converted", "diabetes_test_age_converted"],
                name = "convert_age_node"
            ),
            node(
                func = final_quality_check,
                inputs = ["diabetes_train_age_converted", "diabetes_test_age_converted"],
                outputs = ["diabetes_train_cleaned", "diabetes_test_cleaned"],
                name = "final_quality_check_node"
            ),
        ]
    )