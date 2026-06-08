# Pipeline 5: Prediction

**Pipeline ID** : `prediction`  
**Location**    : `src/diabetes_dss/pipelines/prediction/`  
**Kedro command**: `kedro run --pipeline prediction`  
**Reads**       : `data/06_models/` and `data/08_reporting/model_metadata.json`  
**Writes**      : nothing to disk — all outputs are in-memory

---

## 1. Purpose

The Prediction pipeline is the inference engine of the system. It is called
by the FastAPI backend every time a healthcare worker submits a new patient's
data through the web interface. It takes raw patient input, applies all the
transformations used during training, runs the model, assigns a clinical risk
band, and generates a SHAP explanation — all in a single pipeline run.

Unlike the other four pipelines which process batches of CSV data, this
pipeline processes **one patient at a time** and returns a structured JSON
response.

---

## 2. What Artifacts Are Loaded

All these files were saved by the training and evaluation pipelines:

| Artifact | File | Created By |
|----------|------|------------|
| `trained_model` | `data/06_models/trained_model.pkl` | training pipeline |
| `scaler` | `data/06_models/scaler.pkl` | feature_engineering pipeline |
| `shap_explainer` | `data/06_models/shap_explainer.pkl` | evaluation pipeline |
| `model_metadata` | `data/08_reporting/model_metadata.json` | training pipeline |

Nothing is retrained or refitted — only `.transform()` and `.predict_proba()`
are called on already-fitted objects.

---

## 3. Node-by-Node Description

### Node 1 — `validate_patient_input_node`

**Function**: `validate_patient_input`

**What it does**: Runs validation checks on the raw patient dict from the
API request before any transformation is applied.

**Checks**:

| Check | Details |
|-------|---------|
| Required fields present | `age`, `sex`, `is_pregnant`, `bmi`, `bmi_category`, `family_history_diabetes`, `previous_gdm`, `physically_active`, `has_hypertension`, `residence` |
| Numerical ranges | Age 18–100, BMI 10–80, glucose 30–600, HbA1c 3–20, etc. (WHO/ADA ranges) |
| Categorical values | `sex` ∈ {male, female}, `bmi_category` ∈ {normal, overweight, obese i, obese ii+}, `residence` ∈ {urban, rural} |
| Boolean values | Any of: true/false, 1/0, yes/no (case-insensitive) |

All validation errors are collected before raising so the API caller sees
the full list at once — not just the first error.

**On failure**: Raises `ValueError` → FastAPI returns HTTP 422 with the error message.

---

### Node 2 — `preprocess_patient_input_node`

**Function**: `preprocess_patient_input`

**What it does**:

1. Applies the same categorical encodings used in `data_processing`:
   - `sex`: female→0, male→1
   - `bmi_category`: normal→0, overweight→1, obese i→2, obese ii+→3
   - `residence`: rural→0, urban→1
2. Builds a single-row DataFrame with columns in the **exact order** the model
   was trained on (from `model_metadata["feature_names"]`)
3. Fills any missing optional lab columns with `NaN` (imputed by the scaler)
4. Calls `scaler.transform()` — **never** `fit_transform()`

**Why column order matters**: The model's internal weights are indexed by
position. If columns arrive in a different order than during training, every
prediction will be wrong — silently. Using `feature_names` from
`model_metadata` guarantees correct ordering.

---

### Node 3 — `run_prediction_node`

**Function**: `run_prediction`

**What it does**: Calls `trained_model.predict_proba()` on the scaled
single-row feature DataFrame. Returns:

- `predicted_class` — integer (0, 1, or 2)
- `predicted_label` — string ("Normal", "Prediabetes", or "Diabetic")
- `probabilities` — dict of {class_label: probability} for all 3 classes
- `prob_array` — numpy array (needed by the next node)

---

### Node 4 — `classify_risk_band_node`

**Function**: `classify_risk_band`

**What it does**: Applies the Youden-J optimal threshold (saved in
`model_metadata["threshold"]` by the training pipeline) to `P(Diabetic)`
to assign a clinical risk band.

**Risk bands**:

| Band | Condition | Color | Clinical Action |
|------|-----------|-------|----------------|
| **Low** | P(Diabetic) < `thresh_low_high` | 🟢 Green | Routine annual screening |
| **Moderate** | `thresh_low_high` ≤ P(Diabetic) < `thresh_high` | 🟡 Amber | Lifestyle counselling + rescreen in 3 months |
| **High** | P(Diabetic) ≥ `thresh_high` | 🔴 Red | Urgent referral + confirmatory lab tests |

**Why `thresh_high = thresh_low_high + 0.20`?**  
The Youden-J threshold is the single best operating point for separating
Diabetic from Non-Diabetic. Adding 0.20 creates a high-confidence zone —
patients in this zone have a much higher probability of being diabetic and
warrant immediate action rather than counselling alone.

---

### Node 5 — `explain_prediction_node`

**Function**: `explain_prediction`

**What it does**: Loads the fitted SHAP explainer and computes SHAP values
for the single patient's feature row, for the **Diabetic class**.

**Output format**:

```json
{
  "top_risk_factors": [
    {"feature": "bmi", "value": 0.72, "shap": 0.31, "direction": "increases_risk"},
    {"feature": "age", "value": 0.85, "shap": 0.18, "direction": "increases_risk"}
  ],
  "top_protective_factors": [
    {"feature": "physically_active", "value": 1.0, "shap": -0.09, "direction": "decreases_risk"}
  ],
  "base_value": 0.4821
}
```

Note: feature values are in the **scaled** [0,1] range. The frontend maps
them back to raw clinical values using the scaler's `data_min_` and `data_max_`
attributes for display purposes.

---

### Node 6 — `build_prediction_response_node`

**Function**: `build_prediction_response`

**What it does**: Assembles all node outputs into the final JSON response
that the FastAPI endpoint returns to the frontend.

**Full response schema**:

```json
{
  "predicted_class"       : 2,
  "predicted_label"       : "Diabetic",
  "probabilities"         : {"Normal": 0.08, "Prediabetes": 0.14, "Diabetic": 0.78},
  "risk_band"             : "High",
  "risk_color"            : "#E74C3C",
  "p_diabetic"            : 0.78,
  "risk_description"      : "P(Diabetic) = 0.780 ≥ 0.682. Urgent referral recommended...",
  "opt_threshold"         : 0.4821,
  "top_risk_factors"      : [...],
  "top_protective_factors": [...],
  "shap_base_value"       : 0.4821,
  "patient_input"         : {"age": 57, "sex": "male", "bmi": 29.1, ...}
}
```

---

## 4. Parameters (`conf/base/parameters.yml`)

```yaml
prediction:
  feature_names:
    - age
    - sex
    - is_pregnant
    - bmi
    - bmi_category
    - family_history_diabetes
    - previous_gdm
    - physically_active
    - has_hypertension
    - residence
```

---

## 5. Catalog Entries (add to `catalog.yml`)

```yaml
raw_patient:
  type: memory.MemoryDataset

validated_patient:
  type: memory.MemoryDataset

patient_features:
  type: memory.MemoryDataset

prediction_output:
  type: memory.MemoryDataset

risk_band_output:
  type: memory.MemoryDataset

explanation_output:
  type: memory.MemoryDataset

prediction_response:
  type: memory.MemoryDataset
```

---

## 6. How the FastAPI Backend Calls This Pipeline

```python
# backend/app/ml/predictor.py

from kedro.framework.session import KedroSession
from kedro.framework.startup import bootstrap_project
from pathlib import Path

PROJECT_PATH = Path("../model/kedro_project")
bootstrap_project(PROJECT_PATH)

def predict(patient_dict: dict) -> dict:
    with KedroSession.create(project_path=PROJECT_PATH) as session:
        # Inject the patient data into the catalog
        session.run(
            pipeline_name = "prediction",
            extra_params  = {"raw_patient": patient_dict},
        )
        # Retrieve the response from the catalog
        catalog  = session.load_context().catalog
        response = catalog.load("prediction_response")
    return response
```

---

## 7. Pipeline Registry — Final State

All five pipelines are now registered in `pipeline_registry.py`:

```python
return {
    "data_processing"     : data_processing_pipeline,
    "feature_engineering" : feature_engineering_pipeline,
    "training"            : training_pipeline,
    "evaluation"          : evaluation_pipeline,
    "prediction"          : prediction_pipeline,   

    "__default__": (
        data_processing_pipeline
        + feature_engineering_pipeline
        + training_pipeline
        + evaluation_pipeline
        # prediction is NOT chained here — it runs independently per patient
    ),
}
```

The `prediction` pipeline is intentionally excluded from `__default__` because
it operates on a single patient at runtime, not on batch CSV files. Including
it in `__default__` would cause `kedro run` to fail due to the missing
`raw_patient` dataset.