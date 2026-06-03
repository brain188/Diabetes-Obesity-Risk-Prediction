# Pipeline 1: Data Processing

**Pipeline ID** : `data_processing`  
**Location**    : `src/diabetes_dss/pipelines/data_processing/`  
**Kedro command**: `kedro run --pipeline data_processing`  
**Runs before** : `training` (next pipeline)

---

## 1. Purpose

The Data Processing pipeline is the **entry point** for all raw patient data.
Its job is to transform two raw CSV files — `diabetes_train.csv`
(10,000 records) and `diabetes_test.csv` (2,000 records) — into two clean,
fully numeric Parquet files that are ready for the training pipeline.

Every transformation in this pipeline is deterministic and reproducible. Given
the same raw inputs, it will always produce identical outputs. This is the
foundation of production-ready ML.

---

## 2. Data Split Strategy

```
diabetes_train.csv  (10,000 rows)
       │
       ├── 80% ──► actual training data   (8,000 rows)   — model learns here
       └── 20% ──► validation split       (2,000 rows)   — tuning decisions here

diabetes_test.csv   (2,000 rows)
       └──────────────────────────────────────────────── final evaluation ONLY
```

---

## 3. Column Selection

The raw dataset has **40 columns**. This pipeline keeps only **11** — the
agreed feature set plus the target.

### Columns KEPT

| Column | Type | Role | Why |
|--------|------|------|-----|
| `age` | Continuous | Feature | Risk increases with age; beta-cell function declines |
| `sex` | Binary | Feature | Men/women have different risk thresholds and hormonal profiles |
| `is_pregnant` | Boolean | Feature | Pregnancy induces GDM risk; strong predictor for women |
| `bmi` | Continuous | Feature | Strongest modifiable risk factor; obesity drives insulin resistance |
| `bmi_category` | Ordinal | Feature | Captures the non-linear obesity threshold effect |
| `family_history_diabetes` | Boolean | Feature | Genetic predisposition — one of the strongest predictors |
| `previous_gdm` | Boolean | Feature | History of gestational diabetes → 50–70% develop T2D within 10 years |
| `physically_active` | Boolean | Feature | Exercise is protective — increases muscle glucose uptake |
| `has_hypertension` | Boolean | Feature | Shares root causes with T2D; 75% of diabetics have hypertension |
| `residence` | Binary | Feature | Urban lifestyle → processed food, sedentary work, higher risk |
| `diabetes_status` | Ordinal | **TARGET** | What we are predicting |

### Columns DROPPED and Why

| Column | Reason |
|--------|--------|
| `patient_id` | Pure identifier — no predictive signal |
| `education` | Outside the agreed feature set for this model version |
| `parity`, `previous_macrosomia`, `pcos`, `hiv_positive` | Outside the agreed feature set |
| `diagnosed`, `years_since_diagnosis`, `on_medication`, `medication_type`, `adherence` | **Target leakage** — these describe post-diagnosis facts, not risk factors |
| `retinopathy`, `nephropathy`, `neuropathy`, `cardiovascular_disease`, `diabetic_foot_ulcer`, `microalbuminuria`, `creatinine_mg_dl` | **Target leakage** — long-term complications of diabetes, not predictors of onset |
| `preeclampsia`, `cesarean_delivery`, `macrosomic_baby`, `neonatal_hypoglycemia`, `nicu_admission` | Post-event obstetric outcomes |

---

## 4. Node-by-Node Description

### Node 1 — `load_and_inspect_node`

**Function**: `load_and_inspect`  
**What it does**: Logs the shape, column list, target distribution, and
missing value counts for both datasets. No data is modified.  
**Why**: Provides a visible audit trail. Anyone who runs the pipeline can
immediately confirm the correct files were loaded.

---

### Node 2 — `select_columns_node`

**Function**: `select_columns`  
**What it does**: Retains only the 11 agreed columns; drops all others.  
**Why**: Eliminates target leakage, PII, and irrelevant columns before any
downstream processing.  
**Parameter**: `params:data_processing.columns_to_keep`

---

### Node 3 — `drop_duplicates_node`

**Function**: `drop_duplicates`  
**What it does**: Removes exact duplicate rows using `keep='first'`.  
**Why**: Duplicate rows bias the model. In the training set, 23 duplicates
were found (from multi-hospital data collection). Even a small number of
duplicates in a clinical dataset can meaningfully distort training.

---

### Node 4 — `encode_target_node`

**Function**: `encode_target`  
**What it does**: Maps `"Normal"` → 0, `"Prediabetes"` → 1, `"Diabetic"` → 2.
Preserves the original string as `diabetes_status_raw`.  
**Why ordinal**: The three classes have a natural clinical severity ordering
(Normal < Prediabetes < Diabetic), which gradient boosting models can exploit.  
**Parameter**: `params:data_processing.target_map`

---

### Node 5 — `encode_booleans_node`

**Function**: `encode_booleans`  
**What it does**: Converts boolean columns from mixed True/False string
representations → integer 1/0.  
**Why**: CSV boolean columns arrive as string literals (`"True"`, `"False"`) or
Python booleans depending on the pandas version used to read the file. Uniform
integers prevent any downstream encoding errors.  
**Parameter**: `params:data_processing.bool_columns`

---

### Node 6 — `encode_bmi_category_node`

**Function**: `encode_bmi_category`  
**What it does**: Maps BMI category strings to ordered integers
(`Normal=0`, `Overweight=1`, `Obese I=2`, `Obese II+=3`).  
**Why**: Preserves the clinical severity order. The model benefits from knowing
that Obese I is more severe than Overweight, not just different from it.  
**Parameter**: `params:data_processing.bmi_map`

---

### Node 7 — `encode_sex_node`

**Function**: `encode_sex`  
**What it does**: Maps `"Female"` → 0, `"Male"` → 1.  
**Why**: Binary encoding is sufficient for a two-category feature. Avoids
the dummy-variable trap.  
**Parameter**: `params:data_processing.sex_map`

---

### Node 8 — `encode_residence_node`

**Function**: `encode_residence`  
**What it does**: Maps `"Rural"` → 0, `"Urban"` → 1.  
**Why**: Urban residence is a socioeconomic proxy for processed food access,
sedentary work, and reduced physical activity — all of which increase T2D risk.
Rapid urbanisation in Cameroon makes this a particularly relevant feature for
this low-resource setting context.  
**Parameter**: `params:data_processing.residence_map`

---

### Node 9 — `convert_age_node`

**Function**: `convert_age`  
**What it does**: Truncates float age values (e.g. 63.2 → 63) to whole-year
integers.  
**Why**: Age is always expressed in whole years clinically. Float ages arise
from CSV precision in the raw data. Converting reduces memory usage and makes
the feature consistent with clinical convention.

---

### Node 10 — `final_quality_check_node`

**Function**: `final_quality_check`  
**What it does**: Asserts:

1. Zero missing values in either split
2. All columns are numeric (no string columns left un-encoded)
3. Target column contains only {0, 1, 2}

Raises `ValueError` and halts the pipeline immediately if any check fails —
the corrupted data is never written to disk.  
**Why**: A quality gate at the end of the processing pipeline means the
training pipeline can trust its inputs unconditionally. It is always better
to fail loudly at the data stage than silently at training.

---

## 5. Parameters (`conf/base/parameters.yml`)

```yaml
data_processing:
  columns_to_keep: [age, sex, is_pregnant, bmi, bmi_category,
                    family_history_diabetes, previous_gdm,
                    physically_active, has_hypertension,
                    residence, diabetes_status]

  target_map:
    normal: 0
    prediabetes: 1
    diabetic: 2

  bool_columns: [is_pregnant, family_history_diabetes, previous_gdm,
                 physically_active, has_hypertension]

  bmi_map:
    normal: 0
    overweight: 1
    obese i: 2
    obese ii+: 3

  sex_map:   {female: 0, male: 1}
  residence_map: {rural: 0, urban: 1}
```

---

## 6. Data Catalog Entries (`conf/base/catalog.yml`)

| Catalog Key | File | Format | Layer |
|-------------|------|--------|-------|
| `diabetes_train_raw` | `data/01_raw/diabetes_train.csv` | CSV | Raw (read-only) |
| `diabetes_test_raw` | `data/01_raw/diabetes_test.csv` | CSV | Raw (read-only) |
| `diabetes_train_cleaned` | `data/02_intermediate/diabetes_train_cleaned.parquet` | Parquet | Intermediate |
| `diabetes_test_cleaned` | `data/02_intermediate/diabetes_test_cleaned.parquet` | Parquet | Intermediate |

Intermediate outputs use **Parquet** (not CSV) because:

- Parquet preserves exact integer dtypes (`int32`, `int64`) — CSV always reads
  back as float64 by default
- Parquet is 3–5× faster to read than CSV for large files
- Parquet is column-oriented and compresses well

---

## 7. Final Output Schema

Both `diabetes_train_cleaned.parquet` and `diabetes_test_cleaned.parquet`
have the following guaranteed schema after this pipeline:

| Column | Dtype | Values |
|--------|-------|--------|
| `age` | int32 | 18 – 85 |
| `sex` | int32 | 0 (Female), 1 (Male) |
| `is_pregnant` | int32 | 0, 1 |
| `bmi` | float64 | 16.0 – 45.0 |
| `bmi_category` | int32 | 0, 1, 2, 3 |
| `family_history_diabetes` | int32 | 0, 1 |
| `previous_gdm` | int32 | 0, 1 |
| `physically_active` | int32 | 0, 1 |
| `has_hypertension` | int32 | 0, 1 |
| `residence` | int32 | 0 (Rural), 1 (Urban) |
| `diabetes_status` | int64 | 0 (Normal), 1 (Prediabetes), 2 (Diabetic) |
| `diabetes_status_raw` | object | "Normal", "Prediabetes", "Diabetic" |

**Zero missing values** in any column. The quality gate enforces this.

---

## 8. Running This Pipeline

```bash
# Run only data_processing
kedro run --pipeline data_processing

# Run and see detailed logs
kedro run --pipeline data_processing --log-level INFO

# Verify the output files were created
ls -lh data/02_intermediate/
```

---

## 9. What Happens Next

The `diabetes_train_cleaned.parquet` output feeds directly into the
**Training pipeline**, which will:

1. Create the 80/20 train/validation split from the cleaned training data
2. Scale features with MinMaxScaler
3. Apply SMOTE to fix class imbalance
4. Train 5 candidate models with 5-fold cross-validation
5. Tune the best model with Optuna
6. Evaluate the final model on the test set