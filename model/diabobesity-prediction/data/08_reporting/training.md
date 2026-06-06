# Pipeline 3: Training

**Pipeline ID** : `training`  
**Location**    : `src/diabetes_dss/pipelines/training/`  
**Kedro command**: `kedro run --pipeline training`  
**Reads from**  : `feature_engineering` outputs (`data/03_primary/`, `data/06_models/`)  
**Writes to**   : `data/06_models/trained_model.pkl`, `data/08_reporting/model_metadata.json`

---

## 1. Purpose

The Training pipeline is the core ML engine of the project. It takes the six
verified, scaled, and balanced arrays from the feature engineering pipeline and
produces exactly one output: the best possible fitted model for predicting
diabetes status (Normal / Prediabetes / Diabetic), saved as a Pickle artifact
ready for the FastAPI backend.

The pipeline enforces a strict discipline:

- Five algorithms are trained and compared
- Select the best based on F1(micro), and AUC-ROC
- The test set is touched exactly once, at the very end
- The model is saved only if it meets all performance thresholds

---

## 2. Data Used

| Array | Source | Rows | Notes |
|-------|--------|------|-------|
| `X_train` / `y_train_final` | feature_engineering | ≈ 17,898 | Post-SMOTE, balanced |
| `X_val` / `y_val_final` | feature_engineering | 2,000 | Real distribution |
| `X_test` / `y_test_final` | feature_engineering | 2,000 | Real distribution — touched once |
| `scaler` | feature_engineering | — | Fitted MinMaxScaler |

---

## 3. Node-by-Node Description

### Node 1 — `train_candidates_node`

**Function**: `train_candidates`

**What it does**: Trains five candidate algorithms. For each:

1. Runs 5-fold stratified cross-validation on `X_train` / `y_train_final`
2. Re-fits the model on the full training set
3. Evaluates on `X_val` / `y_val_final`
4. Logs all metrics to MLflow under `diabetes_dss_training`

**The five candidates**:

| Algorithm | Why included |
|-----------|-------------|
| Logistic Regression | Linear baseline; fast; shows if the problem is linearly separable |
| Random Forest | Bagging ensemble; robust to noise; good feature importance |
| XGBoost | Gradient boosting; typically strongest on tabular data |
| LightGBM | Fast gradient boosting; memory-efficient; good on moderate dataset sizes |
| CatBoost | Ordered boosting; often strong out-of-the-box with minimal tuning |

**Primary evaluation metric: F1-macro**  
F1-macro weights all three classes equally — a missed Prediabetes patient
matters as much as a missed Diabetic patient. Accuracy would be misleading
here because predicting "Diabetic" for everyone achieves 74% accuracy while
completely ignoring Normal and Prediabetes patients.

**Parameters**: `cv_folds=5`, `random_state=42`, `mlflow_experiment_name`

---

### Node 2 — `select_best_model_node`

**Function**: `select_best_model`

**What it does**: Ranks all five candidates by validation F1-macro (tiebreak:
roc_auc_ovr). Prints a ranked comparison table to the logs. Returns the
winner's fitted model, name, and metrics.

**Why the validation set for selection, not CV?**  
Cross-validation gives an unbiased estimate of generalisation ability. The
validation set gives an estimate of actual performance on unseen data in its
true class distribution (74% / 13% / 12%). Both signals are logged; CV F1-mean
is the primary selection criterion because it uses more data and is more stable.

---

### Node 3 — `evaluate_final_model_node`

**Function**: `evaluate_final_model`

**What it does**: Evaluates the tuned model on `X_test` / `y_test_final`. This
is the ONLY time the test set is touched in the entire pipeline.

**Metrics computed**:

| Metric | Definition | Threshold |
|--------|-----------|-----------|
| `f1_macro` | Unweighted mean F1 across 3 classes | ≥ 0.80 |
| `recall_macro` | Unweighted mean recall across 3 classes | ≥ 0.78 |
| `accuracy` | Fraction of correct predictions | ≥ 0.80 |
| `roc_auc_ovr` | One-vs-rest AUC, macro-averaged | ≥ 0.85 |
| `f1_weighted` | Frequency-weighted mean F1 | — (logged, no threshold) |
| `precision_macro` | Unweighted mean precision | — (logged, no threshold) |

**Threshold enforcement**: If any metric falls below its threshold, a
`ValueError` is raised and the pipeline halts. The model is NOT saved.
This prevents a poorly-performing model from ever reaching the backend.

---

### Node 5 — `save_model_artifacts_node`

**Function**: `save_model_artifacts`

**What it does**: Returns the tuned model and a metadata dict to Kedro, which
persists them via the Data Catalog:

- `trained_model` → `data/06_models/trained_model.pkl`
- `model_metadata` → `data/08_reporting/model_metadata.json`

**metadata contents**:
```json
{
  "model_name": "XGBoost",
  "model_version": "1.0.0",
  "feature_names": ["age", "sex", "is_pregnant", "bmi", ...],
  "target_encoding": {"0": "Normal", "1": "Prediabetes", "2": "Diabetic"},
  "test_metrics": {"f1_macro": 0.8312, "accuracy": 0.8450, ...},
  "thresholds_met": true,
  "classification_report": {...}
}
```

---

## 4. Parameters (`conf/base/parameters.yml`)

```yaml
training:
  mlflow_experiment_name : diabetes_dss_training
  cv_folds               : 5
  random_state           : 42
```

---

## 5. Data Catalog Entries

| Catalog Key | File | Format | Description |
|-------------|------|--------|-------------|
| `trained_model` | `data/06_models/trained_model.pkl` | Pickle | Final champion model |
| `model_metadata` | `data/08_reporting/model_metadata.json` | JSON | Metrics + feature list |

---

## 6. MLflow Tracking

Every run in this pipeline is logged to MLflow. To view:

```bash
mlflow ui --backend-store-uri ./mlruns
# Open http://localhost:5000
```

Runs logged:

- `candidate_LogisticRegression` — CV scores + val metrics
- `candidate_RandomForest`
- `candidate_XGBoost`
- `candidate_LightGBM`
- `candidate_CatBoost`
- `final_<BestModelName>` — test set metrics + final model artifact

---

## 7. Running This Pipeline

```bash
# Run only training (requires data_processing + feature_engineering first)
kedro run --pipeline training

# Run all three pipelines in sequence
kedro run

# Start MLflow UI to compare runs
mlflow ui --backend-store-uri ./mlruns

# Verify output files
ls -lh data/06_models/
ls -lh data/08_reporting/
```

---

## 8. What Happens Next

The saved `trained_model.pkl`, `scaler.pkl`, and `model_metadata.json` feed
directly into the **Evaluation pipeline**, which will:

1. Generate SHAP global and per-patient explanations
2. Plot confusion matrices and ROC curves
3. Produce the full evaluation report for the project documentation