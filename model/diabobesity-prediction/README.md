# DiabObesity Prediction — ML Model

[![Powered by Kedro](https://img.shields.io/badge/powered_by-kedro-ffc900?logo=kedro)](https://kedro.org)
[![Python](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/)
[![MLflow](https://img.shields.io/badge/experiment_tracking-mlflow-0194E2.svg)](https://mlflow.org/)
[![CatBoost](https://img.shields.io/badge/model-CatBoost-yellow.svg)](https://catboost.ai/)

---

## Overview

**DiabObesity Prediction** is the machine learning layer of the DiabObesity Clinical Decision Support System (DSS). It is a multi-class classification model that predicts a patient's diabetes risk status — **Normal**, **Prediabetes**, or **Diabetic** — from 10 structured clinical features.

The model was built and managed entirely within a [Kedro](https://kedro.org) project, giving the full ML lifecycle — data ingestion, feature engineering, model training, evaluation, and inference — a reproducible, pipeline-based structure. [MLflow](https://mlflow.org/) is used for experiment tracking across all training runs.

The trained model artifacts (model weights, scaler, SHAP explainer, metadata) are loaded at startup by the FastAPI backend and used to serve real-time predictions via the `/predictions` API.

**Key facts at a glance:**

| Property | Value |
|---|---|
| Task | 3-class classification (Normal / Prediabetes / Diabetic) |
| Final model | CatBoost (v1.0.0) |
| Training records | 10,000 |
| Test records | 2,000 |
| Input features | 10 |
| Test accuracy | 73.05% |
| ROC-AUC (one-vs-rest) | 84.54% |
| Explainability | SHAP TreeExplainer + LIME |
| Framework | Kedro 1.4.0 |

---

## ML Architecture

The diagram below shows the end-to-end architecture of the machine learning system, from raw data ingestion through to the FastAPI inference layer.

![ML Architecture](ml_architecture/ML%20architecture%202.png)

---

## Project Structure

```
diabobesity-prediction/
├── conf/
│   ├── base/
│   │   ├── catalog.yml          # Kedro Data Catalog — all dataset I/O definitions
│   │   ├── parameters.yml       # Pipeline parameters (splits, encodings, thresholds)
│   │   └── mlflow.yml           # MLflow experiment tracking configuration
│   └── local/
│       └── credentials.yml      # Local secrets (not committed)
│
├── data/
│   ├── 01_raw/                  # Original unmodified CSV files
│   ├── 02_intermediate/         # Cleaned Parquet files (data_processing output)
│   ├── 03_primary/              # Feature-engineered arrays (X_train, X_val, X_test, y_*)
│   ├── 04_feature/              # Candidate model results, best model, best metrics
│   ├── 06_models/               # Final trained artifacts (model, scaler, SHAP explainer)
│   └── 08_reporting/            # Evaluation plots and JSON reports
│
├── ml_architecture/
│   └── ML architecture 2.png    # End-to-end system architecture diagram
│
├── notebooks/
│   └── modelling.ipynb          # Exploratory modelling notebook
│
├── src/
│   └── diabobesity_prediction/
│       ├── pipelines/
│       │   ├── data_processing/     # Pipeline 1 — clean & encode raw data
│       │   ├── feature_engineering/ # Pipeline 2 — split, scale, SMOTE
│       │   ├── training/            # Pipeline 3 — candidate selection + tuning
│       │   ├── evaluation/          # Pipeline 4 — metrics, plots, SHAP artifacts
│       │   └── prediction/          # Pipeline 5 — inference on new patients
│       ├── pipeline_registry.py     # Registers all pipelines with Kedro
│       └── settings.py
│
├── tests/
│   └── test_run.py
├── pyproject.toml
└── requirements.txt
```

---

## Kedro Pipeline Architecture

The project is composed of **five modular Kedro pipelines** that form a directed acyclic graph (DAG). The default run (`kedro run`) executes pipelines 1–4 in sequence. Pipeline 5 (Prediction) is a separate runtime used by the FastAPI backend.

```
Raw CSV
   │
   ▼
┌─────────────────────┐
│  1. Data Processing │   → Cleans, encodes, validates → Parquet
└──────────┬──────────┘
           │
           ▼
┌────────────────────────────┐
│  2. Feature Engineering    │   → Splits, scales (MinMax), SMOTE → X/y arrays
└──────────┬─────────────────┘
           │
           ▼
┌──────────────────┐
│   3. Training    │   → Trains 5 candidates, selects best, tunes with Optuna
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│  4. Evaluation   │   → Test metrics, confusion matrix, ROC, SHAP plots, report JSON
└──────────────────┘

┌──────────────────────────────────────────────────┐
│  5. Prediction  (FastAPI inference, runs live)   │
│     Loads model.pkl + scaler.pkl + shap.pkl      │
│     → class probabilities → risk band → SHAP     │
└──────────────────────────────────────────────────┘
```

---

### Pipeline 1 — Data Processing

**ID:** `data_processing` | **Command:** `kedro run --pipeline data_processing`

Takes the two raw CSV files (`diabetes_train.csv`, `diabetes_test.csv`) and produces clean, fully-numeric Parquet files that are ready for feature engineering. Every transformation is deterministic — given the same inputs it always produces identical outputs.

**Data split strategy:**

```
diabetes_train.csv  (10,000 rows)
       ├── 80% ──► training data   (8,000 rows)
       └── 20% ──► validation      (2,000 rows)

diabetes_test.csv   (2,000 rows)  ──► hold-out test set (never seen during training)
```

**Transformations applied (10 nodes):**

| # | Node | What it does |
|---|------|-------------|
| 1 | `load_and_inspect` | Logs shape, columns, target distribution, missing values — audit trail only |
| 2 | `select_columns` | Retains 11 agreed columns; drops 29 others (PII, leakage, out-of-scope) |
| 3 | `drop_duplicates` | Removes exact-duplicate rows (`keep='first'`); 23 found in training set |
| 4 | `encode_target` | Maps `Normal→0`, `Prediabetes→1`, `Diabetic→2`; keeps raw string as `diabetes_status_raw` |
| 5 | `encode_booleans` | Converts `True`/`False` strings → `int 1/0` for 5 boolean columns |
| 6 | `encode_bmi_category` | Maps ordinal BMI categories: `Normal=0`, `Overweight=1`, `Obese I=2`, `Obese II+=3` |
| 7 | `encode_sex` | Maps `Female→0`, `Male→1` |
| 8 | `encode_residence` | Maps `Rural→0`, `Urban→1` |
| 9 | `convert_age` | Truncates float ages to whole-year integers (clinical convention) |
| 10 | `final_quality_check` | **Quality gate** — asserts zero nulls, all-numeric schema, target ∈ {0,1,2} |

**Output schema (both train and test Parquet files):**

| Column | Dtype | Values |
|--------|-------|--------|
| `age` | int32 | 18–85 |
| `sex` | int32 | 0 (Female), 1 (Male) |
| `is_pregnant` | int32 | 0, 1 |
| `bmi` | float64 | 16.0–45.0 |
| `bmi_category` | int32 | 0–3 |
| `family_history_diabetes` | int32 | 0, 1 |
| `previous_gdm` | int32 | 0, 1 |
| `physically_active` | int32 | 0, 1 |
| `has_hypertension` | int32 | 0, 1 |
| `residence` | int32 | 0 (Rural), 1 (Urban) |
| `diabetes_status` | int64 | 0, 1, 2 |

---

### Pipeline 2 — Feature Engineering

**ID:** `feature_engineering` | **Command:** `kedro run --pipeline feature_engineering`

Takes the cleaned Parquet outputs and produces the scaled, balanced feature matrices that the training pipeline consumes.

**Steps:**

1. **Train/validation split** — Stratified 80/20 split (`random_state=42`) preserving class proportions across both subsets.
2. **Feature/target separation** — Drops `diabetes_status` and `diabetes_status_raw` from feature matrices; saves `X_train`, `X_val`, `X_test`, `y_train`, `y_val`, `y_test` as Parquet.
3. **MinMaxScaling** — Fits `MinMaxScaler` on `X_train` only; applies to `X_val` and `X_test` without refitting. The fitted scaler is saved as `data/06_models/scaler.pkl` for use in inference.
4. **SMOTE** (Synthetic Minority Over-sampling Technique) — Applied to the training set only to correct class imbalance (`k_neighbors=5`, `random_state=42`). `X_val` and `X_test` are never resampled — they retain the true patient distribution.

**Why SMOTE here?** The dataset is heavily imbalanced (Diabetic class dominates). Without SMOTE, tree models maximise accuracy by over-predicting Diabetic and under-predicting Prediabetes and Normal. SMOTE synthetic samples give minority classes fair representation during training without distorting the evaluation sets.

---

### Pipeline 3 — Training

**ID:** `training` | **Command:** `kedro run --pipeline training`

Trains five candidate algorithms, selects the best by validation F1-macro, and logs all runs to MLflow.

**Candidate algorithms:**

| Model | Configuration |
|-------|--------------|
| Logistic Regression | `C=1.0`, `class_weight='balanced'`, `solver='lbfgs'`, `max_iter=1000` |
| Random Forest | `n_estimators=200`, `max_depth=10`, `min_samples_leaf=5`, `class_weight='balanced'` |
| XGBoost | `n_estimators=200`, `max_depth=6`, `learning_rate=0.05`, `subsample=0.8` |
| LightGBM | `n_estimators=200`, `max_depth=6`, `learning_rate=0.05`, `num_leaves=63` |
| **CatBoost** ✓ | `iterations=200`, `depth=6`, `learning_rate=0.05`, `loss_function='MultiClass'` |

**Selection process:**

1. Each candidate is trained on `X_train` (SMOTE-balanced)
2. Evaluated on `X_val` (real distribution) using **F1-macro** as the primary metric — it treats all three classes equally regardless of frequency
3. 5-fold stratified cross-validation is run on the training set to estimate generalisation
4. The candidate with the highest validation F1-macro is selected
5. **CatBoost** was selected as the best candidate
6. Optuna hyperparameter search is run on the best candidate to further tune it

**Validation metrics of the selected model (CatBoost before final tuning):**

| Metric | Value |
|--------|-------|
| Accuracy | 73.45% |
| F1-macro | 61.05% |
| F1-weighted | 76.10% |
| Precision-macro | 59.00% |
| Recall-macro | 66.02% |
| ROC-AUC (OVR) | 83.93% |

All runs are tracked under the `diabetes_training_experiment` MLflow experiment.

---

### Pipeline 4 — Evaluation

**ID:** `evaluation` | **Command:** `kedro run --pipeline evaluation`

Evaluates the final trained model on the hold-out test set (`diabetes_test.csv`, 2,000 records). No retraining happens here. Produces plots, a fitted SHAP explainer, and a comprehensive JSON report.

**Nodes:**

| # | Node | Output |
|---|------|--------|
| 1 | `compute_test_metrics` | Full metric suite on test set |
| 2 | `plot_confusion_matrix` | Raw + row-normalised confusion matrix (`confusion_matrix.png`) |
| 3 | `plot_roc_curves` | Per-class ROC curves with AUC annotations (`roc_curves.png`) |
| 4 | `compute_shap_values` | SHAP bar chart + beeswarm plot (`shap_bar.png`, `shap_beeswarm.png`) |
| 5 | `save_shap_explainer` | Fitted SHAP TreeExplainer artifact (`shap_explainer.pkl`) |
| 6 | `build_evaluation_report` | Full JSON report (`full_evaluation_report.json`) |

**Test set performance (CatBoost, 2,000 records):**

| Metric | Value |
|--------|-------|
| Accuracy | **73.05%** |
| F1-macro | **61.71%** |
| F1-weighted | **75.77%** |
| Precision-macro | **59.90%** |
| Recall-macro | **66.64%** |
| ROC-AUC (one-vs-rest) | **84.54%** |

**Per-class breakdown:**

| Class | Precision | Recall | F1-score | Support |
|-------|-----------|--------|----------|---------|
| Normal | 0.5431 | 0.6996 | 0.6115 | 243 |
| Prediabetes | 0.3075 | 0.5250 | 0.3879 | 280 |
| Diabetic | **0.9462** | **0.7745** | **0.8518** | 1,477 |
| **Macro avg** | **0.5990** | **0.6664** | **0.6171** | 2,000 |
| **Weighted avg** | **0.8078** | **0.7305** | **0.7577** | 2,000 |

> **Interpretation**: The model is strongest on the Diabetic class (F1 = 0.85, AUC very high), which is the most clinically critical outcome. Prediabetes is the hardest class to predict, which is expected — it is an intermediate state with overlapping clinical features.

---

### Pipeline 5 — Prediction (Inference)

**ID:** `prediction` | **Usage:** Called at runtime by the FastAPI backend

This pipeline is not part of the default training run. It is a separate inference pipeline that accepts a single patient's features and returns a full prediction response.

**What it does (per request):**

1. Receives raw patient feature values as a dictionary
2. Validates inputs (feature names, types, ranges)
3. Applies the fitted `MinMaxScaler` (loaded from `scaler.pkl`)
4. Runs the CatBoost model to get class probabilities for Normal / Prediabetes / Diabetic
5. Applies the Youden-J optimised threshold to assign a **risk band**
6. Computes a per-patient **SHAP waterfall explanation** using the saved explainer
7. Computes a **LIME local explanation** for model interpretability
8. Returns a structured JSON response to the FastAPI endpoint

**Risk band thresholds (Youden-J optimised):**

| Risk Band | Condition | Clinical meaning |
|-----------|-----------|-----------------|
| Low | P(Diabetic) < 0.3472 | Unlikely diabetic; routine screening |
| Moderate | 0.3472 ≤ P(Diabetic) < 0.5472 | Elevated risk; closer monitoring recommended |
| High | P(Diabetic) ≥ 0.5472 | High probability of diabetes; clinical review warranted |

> **Why Youden-J?** The J statistic (Sensitivity + Specificity − 1) maximises both sensitivity (0.8451) and specificity (0.8193) simultaneously, giving an optimal threshold that minimises both missed patients and false alarms. This is more appropriate in a clinical screening context than the default 0.5 threshold.

---

## Dataset

| Property | Value |
|---|---|
| Source | Clinical patient records (Cameroon low-resource hospital setting) |
| Training records | 10,000 |
| Test records | 2,000 |
| Raw columns | 40 |
| Used features | 10 (after leakage removal and column selection) |
| Target classes | Normal (0), Prediabetes (1), Diabetic (2) |
| Class imbalance | Heavy — Diabetic class dominates; corrected by SMOTE in training |

> **Data is not committed to this repository.** Place raw files in `data/01_raw/` before running the pipeline (see [Getting Started](#getting-started)).

---

## Input Features

These 10 features are the inputs to every prediction:

| Feature | Type | Clinical rationale |
|---------|------|--------------------|
| `age` | Continuous (int) | Risk increases with age; beta-cell function declines over time |
| `sex` | Binary (0=F, 1=M) | Sex-specific hormonal profiles affect insulin sensitivity |
| `is_pregnant` | Binary | Pregnancy induces gestational diabetes risk |
| `bmi` | Continuous (float) | Strongest modifiable risk factor; drives insulin resistance |
| `bmi_category` | Ordinal (0–3) | Captures non-linear obesity threshold effects |
| `family_history_diabetes` | Binary | Genetic predisposition — one of the strongest single predictors |
| `previous_gdm` | Binary | History of gestational diabetes → 50–70% develop T2D within 10 years |
| `physically_active` | Binary | Exercise is protective — increases muscle glucose uptake |
| `has_hypertension` | Binary | Shares metabolic root causes with T2D; 75% of diabetics have hypertension |
| `residence` | Binary (0=Rural, 1=Urban) | Urban lifestyle proxy for processed food and sedentary work |

---

## Model Selection & Explainability

### Why CatBoost?

CatBoost was selected over four other candidates because it achieved the highest validation F1-macro score. Key advantages for this task:

- **Ordered boosting** — reduces overfitting on small datasets without extensive tuning
- **Strong out-of-the-box performance** on tabular data with mixed numeric/ordinal features
- **Native multi-class support** with `MultiClass` loss function
- **Full SHAP TreeExplainer compatibility** — exact Shapley values computed in polynomial time

### Explainability

The model provides two types of explanation for every prediction:

**SHAP (SHapley Additive exPlanations)**

- Global view: Bar chart and beeswarm plot showing mean absolute feature contributions across all test patients
- Per-patient view: Waterfall plot showing each feature's positive/negative contribution to this specific prediction
- Implementation: `shap.TreeExplainer` (exact algorithm for tree-based models); fitted once during evaluation and saved as `shap_explainer.pkl`

**LIME (Local Interpretable Model-agnostic Explanations)**

- Fits a locally linear model around each individual prediction
- Provides a different, complementary perspective on feature contributions
- Background dataset saved as `lime_background.pkl`

Both explanations are returned as part of every API prediction response.

---

## Artifacts

All artifacts produced by the pipeline are saved to the `data/` directory (not committed):

| Artifact | Path | Used by |
|----------|------|---------|
| Trained model | `data/06_models/trained_model.pkl` | FastAPI prediction endpoint |
| MinMaxScaler | `data/06_models/scaler.pkl` | FastAPI — scales new patient inputs |
| SHAP explainer | `data/06_models/shap_explainer.pkl` | FastAPI — per-patient SHAP waterfall |
| LIME background | `data/06_models/lime_background.pkl` | FastAPI — LIME local explanations |
| Model metadata | `data/08_reporting/model_metadata.json` | FastAPI `/analytics/model/info` endpoint |
| Full eval report | `data/08_reporting/full_evaluation_report.json` | FastAPI model info endpoint |
| Confusion matrix | `data/08_reporting/confusion_matrix.png` | Chapter 4 reporting |
| ROC curves | `data/08_reporting/roc_curves.png` | Chapter 4 reporting |
| SHAP bar chart | `data/08_reporting/shap_bar.png` | Chapter 4 reporting |
| SHAP beeswarm | `data/08_reporting/shap_beeswarm.png` | Chapter 4 reporting |
| Feature importance | `data/08_reporting/feature_importance.png` | Chapter 4 reporting |
| LIME explanation | `data/08_reporting/lime_explanation.png` | Chapter 4 reporting |

---

## Getting Started

### Prerequisites

- Python 3.11+
- `uv` (recommended) or `pip`
- Raw data files in `data/01_raw/`

### Installation

**Using uv (recommended):**
```bash
uv sync
```

**Using pip:**
```bash
pip install -r requirements.txt
```

**Install the project package in editable mode:**
```bash
pip install -e .
```

### Verify the installation

```bash
kedro info
kedro pipeline list
```

---

## Running Pipelines

**Run the full training pipeline (data processing → feature engineering → training → evaluation):**
```bash
kedro run
```

**Run individual pipelines:**
```bash
# Step 1 — clean the raw data
kedro run --pipeline data_processing

# Step 2 — engineer features, scale, SMOTE
kedro run --pipeline feature_engineering

# Step 3 — train candidate models, select and tune the best
kedro run --pipeline training

# Step 4 — evaluate on test set, generate plots and SHAP artifacts
kedro run --pipeline evaluation
```

**Visualise the pipeline DAG:**
```bash
kedro viz
```
This opens an interactive graph in the browser showing all nodes, datasets, and their connections.

**Run with verbose logging:**
```bash
kedro run --log-level INFO
```

---

## MLflow Experiment Tracking

Training runs are logged to MLflow under the experiment `diabetes_training_experiment`. Each candidate model gets its own run with metrics, parameters, and the fitted model artifact logged automatically.

**Start the MLflow UI:**
```bash
mlflow ui
```
Then open `http://localhost:5000` to compare runs.

The MLflow configuration is in `conf/base/mlflow.yml`:
```yaml
tracking:
  experiment:
    name: diabetes_training_experiment
  run:
    nested: true
```

---

## Integration with the FastAPI Backend

The FastAPI backend (`backend/`) loads the Kedro-produced artifacts at startup and uses them to serve real-time predictions. The connection points are:

| Kedro artifact | Backend usage |
|---|---|
| `data/06_models/trained_model.pkl` | Loaded by `model_loader.py`; called on every `/predictions` request |
| `data/06_models/scaler.pkl` | Applied to incoming patient features before inference |
| `data/06_models/shap_explainer.pkl` | Used by the SHAP explanation endpoint |
| `data/06_models/lime_background.pkl` | Used by the LIME explanation endpoint |
| `data/08_reporting/full_evaluation_report.json` | Served by `GET /analytics/model/info` |
| `data/08_reporting/model_metadata.json` | Powers the `/analytics/feature-importance` endpoint |

The backend's `model_loader.py` caches all artifacts at startup so there is zero I/O overhead per prediction request.

---

## Further Reading

- [Kedro Documentation](https://docs.kedro.org)
- [Kedro Data Catalog](https://docs.kedro.org/en/stable/catalog-data/introduction/)
- [Kedro Pipeline Visualisation](https://docs.kedro.org/en/stable/visualisation/kedro-viz_visualisation.html)
- [CatBoost Documentation](https://catboost.ai/docs/)
- [SHAP Documentation](https://shap.readthedocs.io/)
- [MLflow Documentation](https://mlflow.org/docs/latest/index.html)
- [SMOTE — imbalanced-learn](https://imbalanced-learn.org/stable/references/generated/imblearn.over_sampling.SMOTE.html)
