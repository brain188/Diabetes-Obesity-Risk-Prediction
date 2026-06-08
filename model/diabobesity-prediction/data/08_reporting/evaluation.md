# Pipeline 4: Evaluation

**Pipeline ID** : `evaluation`  
**Location**    : `src/diabetes_dss/pipelines/evaluation/`  
**Kedro command**: `kedro run --pipeline evaluation`  
**Reads from**  : `training` outputs + `feature_engineering` outputs  
**Writes to**   : `data/08_reporting/` and `data/06_models/shap_explainer.pkl`

---

## 1. Purpose

The Evaluation pipeline produces all the evidence needed to document and
validate the final model. It reads the already-trained model from disk —
no retraining or refitting happens here — and generates:

- A full metric suite on the test set
- Confusion matrix plots (raw + normalised)
- Per-class ROC curves
- SHAP global feature importance plots (bar + beeswarm)
- A fitted SHAP explainer artifact for the FastAPI backend
- A single comprehensive JSON evaluation report

---

## 2. Node-by-Node Description

### Node 1 — `compute_test_metrics_node`

**Function**: `compute_test_metrics`

**What it does**: Runs the final trained model on `X_test` / `y_test_final`
and computes all six evaluation metrics plus the full per-class classification
report.

**Metrics**:

| Metric | Description |
|--------|-------------|
| `accuracy` | Overall fraction of correct predictions |
| `f1_macro` | Unweighted mean F1 across all 3 classes — primary metric |
| `f1_weighted` | Frequency-weighted mean F1 |
| `precision_macro` | Unweighted mean precision |
| `recall_macro` | Unweighted mean recall — minimises missed patients |
| `roc_auc_ovr` | One-vs-rest macro AUC — overall discriminative ability |

**Per-class report** (Normal / Prediabetes / Diabetic):
precision, recall, F1, support for each class individually.

---

### Node 2 — `plot_confusion_matrix_node`

**Function**: `plot_confusion_matrix`

**What it does**: Produces a side-by-side figure:

- **Left panel** — raw prediction counts (TP, FP, FN, TN for each class)
- **Right panel** — row-normalised proportions (per-class recall at a glance)

**Why two panels?**  
Raw counts show how many patients were misclassified in absolute terms.
Normalised proportions compare class-level performance fairly despite the
heavy class imbalance (1,477 Diabetic vs 243 Normal in the test set).

**Saved**: `data/08_reporting/confusion_matrix.png`

---

### Node 3 — `plot_roc_curves_node`

**Function**: `plot_roc_curves`

**What it does**: Plots one ROC curve per class using a one-vs-rest strategy,
with AUC scores annotated in the legend.

**Why per-class ROC curves?**  
The macro-averaged AUC scalar hides class-level differences. Plotting each
class separately reveals that the model discriminates Diabetic cases much
better (high AUC) than Prediabetes cases (lower AUC, as expected given the
feature set used). This is important information for clinical interpretation.

**Saved**: `data/08_reporting/roc_curves.png`

---

### Node 4 — `compute_shap_values_node`

**Function**: `compute_shap_values`

**What it does**: Computes SHAP values for all test patients and generates
two global explanation plots:

**Plot 1 — SHAP bar chart** (`shap_bar.png`):  
Mean absolute SHAP value per feature, broken out by class. Shows which
features drive predictions toward each class on average.

**Plot 2 — SHAP beeswarm** (`shap_beeswarm.png`):  
Each dot = one patient. Position on X-axis = SHAP value (impact on the
Diabetic class prediction). Color = raw feature value (red = high, blue = low).
This reveals not just which features matter but HOW they matter — e.g., "high
BMI increases the Diabetic prediction".

**Why TreeExplainer?**  
TreeExplainer is a fast, exact SHAP algorithm for tree-based models
(CatBoost, XGBoost, LightGBM, Random Forest). It computes exact Shapley
values in polynomial time. A KernelExplainer fallback is included for
non-tree models.

**Saved**: `data/08_reporting/shap_bar.png`, `data/08_reporting/shap_beeswarm.png`

---

### Node 5 — `save_shap_explainer_node`

**Function**: `save_shap_explainer`

**What it does**: Fits the SHAP explainer on the training data and returns
it for Kedro to persist as a Pickle artifact.

**Why save it here?**  
The FastAPI prediction endpoint needs to generate a per-patient SHAP
waterfall explanation for every prediction it serves. Fitting the explainer
on every request would be slow. By saving it once here, the backend loads
it at startup and reuses it across all requests — zero overhead per prediction.

**Saved**: `data/06_models/shap_explainer.pkl`

---

### Node 6 — `build_evaluation_report_node`

**Function**: `build_evaluation_report`

**What it does**: Compiles `test_metrics_output` and `model_metadata` into
one comprehensive JSON report.

**Report contents**:

```json
{
  "model_name": "CatBoost",
  "model_version": "1.0.0",
  "feature_names": ["age", "sex", "bmi", ...],
  "n_features": 10,
  "target_encoding": {"0": "Normal", "1": "Prediabetes", "2": "Diabetic"},
  "test_metrics": {
    "accuracy": 0.7520,
    "f1_macro": 0.5630,
    ...
  },
  "classification_report": {
    "Normal": {"precision": 0.53, "recall": 0.61, ...},
    "Prediabetes": {"precision": 0.27, "recall": 0.23, ...},
    "Diabetic": {"precision": 0.88, "recall": 0.87, ...}
  },
  "threshold": {
    "opt_threshold": 0.4821,
    "thresh_low_high": 0.4821,
    "thresh_high": 0.6821,
    "description": {
      "low": "P(Diabetic) < 0.4821",
      "moderate": "0.4821 <= P(Diabetic) < 0.6821",
      "high": "P(Diabetic) >= 0.6821"
    }
  },
  "evaluation_summary": {
    "f1_macro": "0.5630 — unweighted mean F1 across all 3 classes",
    ...
  }
}
```

**Saved**: `data/08_reporting/full_evaluation_report.json`

---

## 3. Catalog Entries (add to `catalog.yml`)

```yaml
confusion_matrix_png:
  type: pickle.PickleDataset
  filepath: data/08_reporting/confusion_matrix.png

roc_curves_png:
  type: pickle.PickleDataset
  filepath: data/08_reporting/roc_curves.png

shap_bar_png:
  type: pickle.PickleDataset
  filepath: data/08_reporting/shap_bar.png

shap_beeswarm_png:
  type: pickle.PickleDataset
  filepath: data/08_reporting/shap_beeswarm.png

shap_explainer:
  type: pickle.PickleDataset
  filepath: data/06_models/shap_explainer.pkl

full_evaluation_report:
  type: json.JSONDataset
  filepath: data/08_reporting/full_evaluation_report.json
```

---

## 4. Catalog Entry — `label_encoder` Removed

The `label_encoder` entry that appeared in `catalog.yml`:

```yaml
label_encoder:
  type: pickle.PickleDataset
  filepath: data/06_models/label_encoder.pkl
```

---

## 5. Running This Pipeline

```bash
# Run only evaluation (requires training to have run first)
kedro run --pipeline evaluation

# Run everything end-to-end
kedro run

# Check output files
ls -lh data/08_reporting/
ls -lh data/06_models/shap_explainer.pkl
```

---

## 6. What Happens Next

The evaluation outputs feed directly into the **Prediction pipeline**, which will:

1. Load `trained_model.pkl`, `scaler.pkl`, `shap_explainer.pkl`,
   `model_metadata.json`, and `full_evaluation_report.json`
2. Accept a new patient's raw feature values
3. Scale them with the fitted scaler
4. Predict the class probabilities
5. Apply the Youden-J threshold to assign a risk band (Low / Moderate / High)
6. Compute a per-patient SHAP waterfall explanation
7. Return the full prediction result as a JSON response to the FastAPI backend