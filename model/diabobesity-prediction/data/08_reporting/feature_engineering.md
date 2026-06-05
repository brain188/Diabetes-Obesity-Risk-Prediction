# Pipeline 2: Feature Engineering

**Pipeline ID** : `feature_engineering`  
**Location**    : `src/diabetes_dss/pipelines/feature_engineering/`  
**Kedro command**: `kedro run --pipeline feature_engineering`  
**Reads from**  : `data_processing` pipeline outputs (`data/02_intermediate/`)  
**Writes to**   : `data/03_primary/` and `data/06_models/`

---

## 1. Purpose

The Feature Engineering pipeline takes the two clean, fully-numeric Parquet
files produced by the data_processing pipeline and transforms them into six
ready-to-train arrays — plus a saved scaler artifact — that the training
pipeline consumes directly.

Three major operations happen here:

1. **Split** — a clean 80/20 stratified train/validation split is created
   from the 10,000-row training file.
2. **Scale** — all features are scaled to [0, 1] using MinMaxScaler fitted
   exclusively on the training subset.
3. **Balance** — SMOTE is applied to the training set to correct the severe
   class imbalance (74% Diabetic / 13% Prediabetes / 12% Normal).

---

## 2. Why No Derived Features?

Earlier iterations of this project included derived features such as
`glucose_bmi_interaction`, `cholesterol_hdl_ratio`, and clinical threshold
flags. After reviewing the pipeline scope, the decision was made to keep the
feature set strictly as-is from the data_processing pipeline:

- The dataset already includes the raw clinical measurements that those derived
  features summarise.
- Tree-based models (XGBoost, LightGBM, Random Forest) discover interaction
  effects internally — explicit interaction terms are redundant.
- Adding derived features increases dimensionality without clear benefit on
  this particular dataset size (10,000 rows, 9 features).

The pipeline is designed to be extended: derived features can be added in a
`compute_derived_features` node between `split_train_validation_node` and
`separate_features_target_node` without changing any other node.

---

## 3. Node-by-Node Description

### Node 1 — `split_train_validation_node`

**Function**: `split_train_validation`

**What it does**: Creates an 80/20 stratified split from `diabetes_train_cleaned`.

**Why stratified?**  
The class distribution is highly imbalanced:

- Class 2 (Diabetic)    : 74.6% of samples
- Class 1 (Prediabetes) : 13.4% of samples
- Class 0 (Normal)      : 12.0% of samples

Without `stratify=y`, a random split could give the validation set only 8%
Normal samples, making validation metrics for that class unreliable. Stratified
splitting guarantees the same ratio in both halves.


**Result**:
```

diabetes_train_cleaned (10,000 rows)
    ├── train_split :  8,000 rows  (80%)
    └── val_split   :  2,000 rows  (20%)
```

**Parameters**: `val_size=0.20`, `random_state=42`

---

### Node 2 — `separate_features_target_node`

**Function**: `separate_features_target`

**What it does**: Drops `diabetes_status` and `diabetes_status_raw` from each
split to produce clean X (features) and y (labels) pairs.

**Columns dropped from X**:

| Column | Reason |
|--------|--------|
| `diabetes_status` | The target — must not be a feature |
| `diabetes_status_raw` | String label kept for reporting only |

**Final feature columns in X** (9 features):

```
age, sex, is_pregnant, bmi, bmi_category,
family_history_diabetes, previous_gdm,
physically_active, has_hypertension, residence
```

---

### Node 3 — `scale_features_node`

**Function**: `scale_features`

**What it does**: Fits `MinMaxScaler` on `X_train` only, then applies
`.transform()` to all three splits.

**Why MinMaxScaler?**  

- Most features are already bounded (age: 18–85, booleans: 0/1, BMI
  category: 0–3). MinMaxScaler maps each to [0, 1] without changing
  the distribution shape.
- Logistic Regression requires scaling — features at very different scales
  cause the gradient to converge poorly.
- Tree-based models are scale-invariant but scaling does not hurt them.

**Why fit on training only?**  
Fitting on the full dataset (train + val + test) would expose the scaler to
validation and test statistics — a subtle form of data leakage. The scaler
must learn only from the training distribution, then apply that
transformation blindly to all other splits.

**Saved artifact**: `data/06_models/scaler.pkl`  
This exact fitted scaler is loaded by the FastAPI backend at inference time to
apply the same transformation to new patient inputs.

---

### Node 4 — `apply_smote_node`

**Function**: `apply_smote`

**What it does**: Applies SMOTE to `X_train_scaled` / `y_train` to equalise
all three class counts.

**Why class imbalance is dangerous**  
With 74.6% Diabetic samples, a model that predicts "Diabetic" for every patient
achieves 74.6% accuracy while completely ignoring Normal and Prediabetes
patients. In a medical screening system this is clinically catastrophic —
those Normal patients would never receive lifestyle interventions.

**Why SMOTE over other strategies?**

| Strategy | Problem |
|----------|---------|
| Do nothing | Model ignores minority classes |
| `class_weight='balanced'` | Reweights but does not add diversity |
| Random oversampling | Creates exact duplicates → overfitting |
| **SMOTE** | Generates new synthetic samples via k-NN interpolation → reduces overfitting, improves minority class recall |
| Undersampling | Throws away 60% of the training data |

**Why ONLY on the training set?**  
Validation and test sets must reflect the real-world class distribution.
Applying SMOTE to them would create an artificially balanced evaluation set
and produce metrics that are impossible to reproduce in a real hospital setting.

**Before and after (approximate)**:

| Class | Before SMOTE | After SMOTE |
|-------|-------------|------------|
| 0 — Normal | 963 (12.0%) | 5,966 (33.3%) |
| 1 — Prediabetes | 1,071 (13.4%) | 5,966 (33.3%) |
| 2 — Diabetic | 5,966 (74.6%) | 5,966 (33.3%) |
| **Total** | **8,000** | **≈ 17,898** |

**Parameters**: `smote_random_state=42`, `smote_k_neighbors=5`

---

### Node 5 — `final_feature_check_node`

**Function**: `final_feature_check`

**What it does**: Runs five assertions before writing any output to disk:

1. Zero missing values in all X matrices and y vectors
2. All feature values are in [0, 1] — confirms scaling was applied
3. Feature column names are identical across train, val, and test
4. Target vectors contain only {0, 1, 2}
5. Logs final shapes and class distributions for the audit trail

Raises `ValueError` and halts the pipeline if any check fails.

---

## 4. Parameters (`conf/base/parameters.yml`)

```yaml
feature_engineering:
  val_size:            0.20
  random_state:        42
  target_col:          diabetes_status
  drop_cols:           [diabetes_status, diabetes_status_raw]
  smote_random_state:  42
  smote_k_neighbors:   5
```

---

## 5. Data Catalog Entries

| Catalog Key | File | Format | Layer |
|-------------|------|--------|-------|
| `X_train` | `data/03_primary/X_train.parquet` | Parquet | Primary |
| `y_train` | `data/03_primary/y_train.parquet` | Parquet | Primary |
| `X_val` | `data/03_primary/X_val.parquet` | Parquet | Primary |
| `y_val` | `data/03_primary/y_val.parquet` | Parquet | Primary |
| `X_test` | `data/03_primary/X_test.parquet` | Parquet | Primary |
| `y_test` | `data/03_primary/y_test.parquet` | Parquet | Primary |
| `scaler` | `data/06_models/scaler.pkl` | Pickle | Models |

---

## 6. Final Output Summary

After this pipeline runs successfully:

| Split | Rows | Columns | Notes |
|-------|------|---------|-------|
| `X_train` | ≈ 17,898 | 9 | Post-SMOTE, scaled to [0, 1] |
| `y_train` | ≈ 17,898 | — | Balanced: 33% each class |
| `X_val` | 2,000 | 9 | Scaled, NO SMOTE — real distribution |
| `y_val` | 2,000 | — | Real distribution: 74% / 13% / 12% |
| `X_test` | 2,000 | 9 | Scaled, NO SMOTE — real distribution |
| `y_test` | 2,000 | — | Real distribution: 73% / 14% / 12% |

---

## 7. Running This Pipeline

```bash
# Run only feature_engineering (requires data_processing to have run first)
kedro run --pipeline feature_engineering

# Run both pipelines in sequence
kedro run --pipeline data_processing
kedro run --pipeline feature_engineering

# Or run both at once using the default pipeline
kedro run

# Check output files
ls -lh data/03_primary/
ls -lh data/06_models/
```

---

## 8. What Happens Next

The six output arrays and the saved scaler feed directly into the
**Training pipeline**, which will:

1. Load `X_train`, `y_train`, `X_val`, `y_val`, `X_test`, `y_test`
2. Train 5 candidate models with 5-fold cross-validation
3. Select the best model based on F1-macro score
4. Tune the best model with Optuna
5. Save only the best model as `model.pkl`
6. Evaluate the final model on the test set