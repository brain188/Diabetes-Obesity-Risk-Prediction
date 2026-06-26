# DiabObesity DSS — Backend API

[![Python](https://img.shields.io/badge/python-3.11-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-latest-009688.svg)](https://fastapi.tiangolo.com/)
[![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-2.0-red.svg)](https://www.sqlalchemy.org/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15-336791.svg)](https://www.postgresql.org/)
[![CatBoost](https://img.shields.io/badge/model-CatBoost_v1.0.0-yellow.svg)](https://catboost.ai/)

---

## Overview

This is the FastAPI backend for the **DiabObesity Intelligent Decision Support System (DSS)** — a clinical tool designed for early risk prediction of Type 2 Diabetes and obesity in low-resource healthcare settings.

The backend serves as the bridge between the React frontend (used by healthcare workers) and the ML model layer (trained with Kedro). It manages patient records, runs screening data through the CatBoost prediction model, generates SHAP/LIME explanations, produces clinical reports, and maintains a full audit trail of all clinical actions.

**What it does at a high level:**

- Authenticates healthcare workers with JWT (access + refresh tokens)
- Manages patient registration and clinical records in PostgreSQL (Supabase)
- Accepts structured screening data and runs it through the CatBoost diabetes risk model
- Returns a risk classification (Normal / Prediabetes / Diabetic), a risk band (Low / Moderate / High), and SHAP + LIME explanations
- Applies rule-based obesity assessment alongside the ML prediction
- Generates PDF clinical reports and stores them per patient
- Exposes analytics endpoints for dashboard statistics, model performance, and audit summaries

---

## Architecture

The backend follows a **four-layer architecture** with strict separation of concerns:

```
┌─────────────────────────────────────────────────────────────┐
│                   React Frontend (port 5173)                │
└───────────────────────────┬─────────────────────────────────┘
                            │  HTTP / JSON (CORS)
                            ▼
┌─────────────────────────────────────────────────────────────┐
│              FastAPI Application  (port 8000)               │
│                                                             │
│  ┌──────────────┐   ┌──────────────┐   ┌────────────────┐  │
│  │  API Routes  │   │   Services   │   │  Repositories  │  │
│  │  /api/v1/    │──▶│  Business    │──▶│  Database      │  │
│  │  auth        │   │  Logic       │   │  Access Layer  │  │
│  │  patients    │   │  auth        │   │  (SQLAlchemy   │  │
│  │  screening   │   │  patient     │   │   async)       │  │
│  │  predictions │   │  screening   │   └────────────────┘  │
│  │  reports     │   │  prediction  │                        │
│  │  notes       │   │  report      │   ┌────────────────┐  │
│  │  analytics   │   │  audit       │   │   ML Module    │  │
│  └──────────────┘   └──────────────┘   │  model_loader  │  │
│                                        │  predictor     │  │
│  ┌──────────────────────────────────┐  │  explainers    │  │
│  │  Core                            │  │  feature_build │  │
│  │  config · database · security    │  │  obesity       │  │
│  │  logging · exceptions · deps     │  └────────────────┘  │
│  └──────────────────────────────────┘                       │
└─────────────────────────────────────────────────────────────┘
              │                          │
              ▼                          ▼
┌─────────────────────┐    ┌────────────────────────────────┐
│  PostgreSQL          │    │  ML Artifacts (Kedro output)   │
│  (Supabase)          │    │  data/06_models/               │
│  • healthcare_workers│    │  ├── trained_model.pkl         │
│  • patients          │    │  ├── scaler.pkl                │
│  • screening_visits  │    │  ├── shap_explainer.pkl        │
│  • screening_data    │    │  └── lime_background.pkl       │
│  • predictions       │    │  data/08_reporting/            │
│  • recommendations   │    │  ├── model_metadata.json       │
│  • shap_explanations │    │  └── full_evaluation_report.json│
│  • clinical_notes    │    └────────────────────────────────┘
│  • reports           │
│  • audit_logs        │
└─────────────────────┘
```

---

## Technology Stack

| Component | Technology | Notes |
|-----------|------------|-------|
| Framework | FastAPI | Async, OpenAPI/Swagger auto-docs |
| ORM | SQLAlchemy 2.0 (async) | `asyncpg` driver for PostgreSQL |
| Database | PostgreSQL 15 (Supabase) | Connection pooler compatible |
| Migrations | Alembic | 3 migration versions |
| Auth | JWT (python-jose) + bcrypt | Access (60 min) + Refresh (7 day) tokens |
| Validation | Pydantic v2 + pydantic-settings | Schema validation and config loading |
| ML Model | CatBoost (v1.0.0) | Loaded from Kedro artifact |
| Explainability | SHAP TreeExplainer + LIME | Pre-loaded at startup |
| Reporting | ReportLab | PDF report generation |
| Containerisation | Docker (multi-stage build) | Non-root user; health check included |
| Testing | pytest + pytest-asyncio | Async test client via httpx |

---

## Project Structure

```
backend/
├── app/
│   ├── main.py                         # FastAPI app, middleware, lifespan, health check
│   ├── api/
│   │   └── v1/
│   │       ├── __init__.py             # Registers all routers under /api/v1
│   │       ├── auth.py                 # Authentication endpoints
│   │       ├── patients.py             # Patient management endpoints
│   │       ├── screening.py            # Screening data entry endpoints
│   │       ├── prediction.py           # ML prediction endpoints
│   │       ├── reports.py              # Clinical report endpoints
│   │       ├── notes.py                # Clinical notes endpoints
│   │       └── analytics.py            # Dashboard and analytics endpoints
│   ├── core/
│   │   ├── config.py                   # All settings via pydantic-settings (.env)
│   │   ├── database.py                 # Async SQLAlchemy engine and session factory
│   │   ├── security.py                 # JWT creation/verification, bcrypt hashing
│   │   ├── dependencies.py             # FastAPI Depends: current user, DB session
│   │   ├── exceptions.py               # Custom exception classes (AppException tree)
│   │   ├── logging.py                  # Structured logging + audit logger
│   │   └── constants.py                # Application-wide constants
│   ├── models/                         # SQLAlchemy ORM models (one file per table)
│   │   ├── base.py                     # TimestampMixin, generate_uuid
│   │   ├── healthcare_worker.py        # healthcare_workers table
│   │   ├── patient.py                  # patients table
│   │   ├── screening_data.py           # screening_visits + screening_data tables
│   │   ├── prediction.py               # predictions table
│   │   ├── recommendation.py           # recommendations table
│   │   ├── explanation.py              # shap_explanations table
│   │   ├── clinical_note.py            # clinical_notes table
│   │   ├── report.py                   # reports table
│   │   └── audit_log.py                # audit_logs table
│   ├── schemas/                        # Pydantic v2 request/response schemas
│   │   ├── auth.py
│   │   ├── patient.py
│   │   ├── screening.py
│   │   ├── prediction.py
│   │   ├── recommendation.py
│   │   ├── report.py
│   │   ├── clinical_note.py
│   │   ├── shap.py
│   │   └── common.py
│   ├── repositories/                   # Database access layer (async SQLAlchemy queries)
│   │   ├── base.py
│   │   ├── healthcare_worker_repository.py
│   │   ├── patient_repository.py
│   │   ├── screening_repository.py
│   │   ├── prediction_repository.py
│   │   ├── report_repository.py
│   │   ├── clinical_note_repository.py
│   │   └── audit_log_repository.py
│   ├── services/                       # Business logic layer
│   │   ├── auth_service.py
│   │   ├── patient_service.py
│   │   ├── screening_service.py
│   │   ├── prediction_service.py
│   │   ├── report_service.py
│   │   ├── clinical_note_service.py
│   │   └── audit_service.py
│   ├── ml/                             # ML inference module
│   │   ├── model_loader.py             # Loads and caches all Kedro artifacts at startup
│   │   ├── diabetes_predictor.py       # Runs CatBoost inference + threshold logic
│   │   ├── explainers.py               # SHAP waterfall + LIME explanations
│   │   ├── feature_builder.py          # Maps raw patient dict → scaled feature vector
│   │   ├── encoders.py                 # Encodes categorical inputs to numeric
│   │   └── obesity.py                  # Rule-based obesity assessment
│   └── utils/
│       ├── pdf_generator.py            # ReportLab PDF builder
│       ├── date_utils.py
│       ├── file_utils.py
│       ├── json_utils.py
│       ├── response_utils.py
│       └── validators.py
├── alembic/                            # Database migration scripts
│   ├── env.py
│   └── versions/
│       ├── 2026_06_17_0001_initial_schema.py        # All 10 tables
│       ├── 2026_06_17_0002_add_is_active_to_patients.py
│       └── 2026_06_18_0003_add_refresh_token_fields.py
├── tests/
│   ├── conftest.py
│   ├── test_auth.py
│   ├── test_patients.py
│   ├── test_screening.py
│   ├── test_predictions.py
│   ├── test_reports.py
│   ├── test_notes.py
│   └── test_analytics.py
├── docker/
│   ├── docker-compose-dev.yml
│   ├── docker-compose-prod.yml
│   ├── nginx/
│   └── postgres/
├── scripts/
│   └── healthcheck.py
├── Dockerfile                          # Multi-stage build (builder + slim runtime)
├── requirements.txt
├── pytest.ini
└── .env                                # Local environment variables (not committed)
```

---

## Database Schema

The database contains **10 tables**, created and managed by Alembic migrations:

| Table | Description |
|-------|-------------|
| `healthcare_workers` | Authenticated system users (clinicians, admins); stores hashed passwords and refresh tokens |
| `patients` | Patient demographic records; soft-deletable via `is_active` flag |
| `screening_visits` | Top-level record for each clinic visit (links patient to a visit date) |
| `screening_data` | Structured clinical measurements collected during a visit (BMI, history flags, etc.) |
| `predictions` | ML prediction results: class probabilities, risk class, risk band, and threshold used |
| `recommendations` | Rule-based clinical recommendations generated for each prediction |
| `shap_explanations` | Per-prediction SHAP feature contribution values stored as JSON |
| `clinical_notes` | Free-text notes written by healthcare workers against a patient or visit |
| `reports` | Generated PDF report metadata and file paths |
| `audit_logs` | Immutable record of every clinical and authentication action for compliance |

All tables use UUID primary keys and carry `created_at` / `updated_at` timestamps via `TimestampMixin`.

---

## API Endpoints

All endpoints are prefixed with `/api/v1`. Authentication (JWT Bearer token) is required on all routes except `/auth/login`, `/auth/register`, `/health`, and `/ready`.

### Authentication — `/api/v1/auth`

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/register` | Register a new healthcare worker account |
| `POST` | `/login` | Log in — returns `access_token` (60 min) + `refresh_token` (7 days) |
| `POST` | `/logout` | Invalidate the current refresh token |
| `POST` | `/refresh` | Exchange a refresh token for a new access token |
| `POST` | `/change-password` | Change the authenticated user's password |
| `POST` | `/password-reset/request` | Request a password reset link |
| `POST` | `/password-reset/confirm` | Confirm password reset with token |
| `GET` | `/profile` | Get the authenticated user's profile |
| `GET` | `/users` | List all registered healthcare workers (admin) |

### Patients — `/api/v1/patients`

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/` | Register a new patient |
| `GET` | `/` | List all patients (paginated) |
| `GET` | `/search` | Search patients by name, ID, or demographic filters |
| `GET` | `/{patient_id}` | Get a patient's full profile |
| `PATCH` | `/{patient_id}` | Update patient details |
| `DELETE` | `/{patient_id}` | Soft-delete a patient (`is_active=false`) |
| `POST` | `/{patient_id}/restore` | Restore a soft-deleted patient |
| `GET` | `/{patient_id}/summary` | Get a patient's clinical summary (visits, latest prediction) |

### Screening — `/api/v1/screening`

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/` | Create a new screening visit for a patient |
| `POST` | `/{visit_id}/data` | Submit structured screening measurements for a visit |
| `GET` | `/` | List all screening visits (paginated) |
| `GET` | `/{visit_id}` | Get a specific screening visit with its data |
| `GET` | `/patients/{patient_id}` | List all screening visits for a patient |
| `PATCH` | `/{visit_id}` | Update screening data for a visit |

### Predictions — `/api/v1/predictions`

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/` | Run the ML prediction pipeline for a screening visit |
| `GET` | `/{prediction_id}` | Get a prediction result with class probabilities and risk band |
| `GET` | `/{prediction_id}/explanations` | Get SHAP + LIME feature explanations for a prediction |
| `GET` | `/{prediction_id}/recommendation` | Get the clinical recommendation for a prediction |
| `GET` | `/patients/{patient_id}/history` | Get the full prediction history for a patient |

### Reports — `/api/v1/reports`

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/` | List all reports |
| `POST` | `/` | Generate a new PDF clinical report for a patient/prediction |
| `GET` | `/{report_id}` | Get report metadata |
| `GET` | `/{report_id}/download` | Download the PDF report file |
| `GET` | `/patients/{patient_id}` | List all reports for a patient |
| `DELETE` | `/{report_id}` | Delete a report |

### Clinical Notes — `/api/v1/notes`

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/` | Create a clinical note |
| `GET` | `/` | List all clinical notes |
| `GET` | `/{note_id}` | Get a specific note |
| `GET` | `/patients/{patient_id}` | List all notes for a patient |
| `GET` | `/visits/{visit_id}` | List all notes for a screening visit |
| `PATCH` | `/{note_id}` | Update a clinical note |
| `DELETE` | `/{note_id}` | Delete a clinical note |

### Analytics — `/api/v1/analytics`

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/stats/dashboard` | Aggregate dashboard statistics (patient counts, prediction distribution) |
| `GET` | `/stats/trends` | Monthly prediction trend data |
| `GET` | `/risk-distribution` | Distribution of patients across risk bands |
| `GET` | `/predictions/summary` | Summary statistics of all predictions |
| `GET` | `/feature-importance` | Global SHAP feature importance from the model |
| `GET` | `/model/info` | Model metadata, version, test metrics, and threshold configuration |
| `GET` | `/audit/summary` | Audit log summary for a given time window |
| `GET` | `/audit/activities` | Recent audit activity feed |
| `GET` | `/audit/user/{worker_id}` | Audit trail for a specific healthcare worker |

### Health Checks

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/health` | Liveness check — returns `{"status": "healthy"}` |
| `GET` | `/ready` | Readiness check — confirms ML model is loaded |

---

## ML Integration

The ML module integrates the CatBoost model trained by the Kedro pipeline. All artifacts are loaded **once at startup** and cached in memory for the lifetime of the process — there is no per-request disk I/O.

### Startup sequence (`lifespan` in `main.py`)

1. `init_database()` — creates the asyncpg connection pool and pings Supabase (30 s timeout)
2. `model_loader.load_all()` — loads `trained_model.pkl`, `scaler.pkl`, `shap_explainer.pkl`, `lime_background.pkl`, `model_metadata.json`
3. Cache warm-up — pre-builds feature importance, SHAP, and LIME explainer caches so the first prediction request is not slow

### Prediction flow (per request)

```
POST /api/v1/predictions/
         │
         ▼
  feature_builder.py   — maps raw patient ScreeningData → 10-feature dict
         │
         ▼
  encoders.py          — converts categorical strings to numeric codes
                         (Sex, BMI category, Residence, booleans)
         │
         ▼
  scaler.pkl           — MinMaxScaler fitted on training data
                         (exact same transformation used during Kedro training)
         │
         ▼
  trained_model.pkl    — CatBoost classifier
                         → P(Normal), P(Prediabetes), P(Diabetic)
         │
         ▼
  Risk band assignment — Youden-J optimised thresholds:
                         Low    : P(Diabetic) < 0.3472
                         Moderate: 0.3472 ≤ P(Diabetic) < 0.5472
                         High   : P(Diabetic) ≥ 0.5472
         │
         ├──▶ shap_explainer.pkl  — per-patient SHAP waterfall values
         │
         ├──▶ lime_background.pkl — LIME local explanation
         │
         └──▶ obesity.py          — rule-based obesity assessment (BMI threshold)
```

The full result is persisted to the `predictions`, `recommendations`, and `shap_explanations` tables, then returned to the frontend as a JSON response.

---

## Configuration

All configuration is loaded from environment variables via `pydantic-settings`. Create a `.env` file in the `backend/` directory before running:

```env
# Application
APP_NAME="Diabetes DSS API"
APP_VERSION="1.0.0"
ENVIRONMENT=development
DEBUG=true

# Server
HOST=0.0.0.0
PORT=8000

# Database (Supabase / PostgreSQL)
DATABASE_URL=postgresql+asyncpg://<user>:<password>@<host>:6543/postgres
DATABASE_POOL_SIZE=10
DATABASE_MAX_OVERFLOW=20

# CORS — list of allowed frontend origins
ALLOWED_ORIGINS=["http://localhost:5173","http://localhost:3000"]

# Authentication
SECRET_KEY=<generate-with: openssl rand -hex 32>
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60
REFRESH_TOKEN_EXPIRE_DAYS=7
BCRYPT_ROUNDS=12

# ML Artifacts — path to Kedro data/ directory
ML_ARTIFACTS_BASE=../model/diabobesity-prediction/data
MODEL_VERSION=1.0.0

# Logging
LOG_LEVEL=INFO
LOG_FILE=logs/app.log

# Reports
REPORTS_DIR=reports
```

> **Never commit `.env` to version control.** Use `.env.example` as the template.

---

## Getting Started

### Prerequisites

- Python 3.11+
- A running PostgreSQL database (or a Supabase project)
- ML artifacts from the Kedro model (`data/06_models/` and `data/08_reporting/`)

### 1. Create a virtual environment

```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# Linux / macOS
source .venv/bin/activate
```

### 2. Install dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 3. Configure environment

```bash
copy .env.example .env    # Windows
cp .env.example .env      # Linux/macOS
# Edit .env with your database URL, secret key, and artifact paths
```

### 4. Run database migrations

```bash
alembic upgrade head
```

### 5. Start the server

```bash
# Development (with auto-reload)
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Production
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

The API will be available at `http://localhost:8000`.  
Interactive docs (Swagger UI) at `http://localhost:8000/docs` (only when `DEBUG=true`).

---

## Database Migrations

Database schema changes are managed with [Alembic](https://alembic.sqlalchemy.org/).

```bash
# Apply all pending migrations
alembic upgrade head

# Roll back the last migration
alembic downgrade -1

# View migration history
alembic history

# Create a new migration (after modifying ORM models)
alembic revision --autogenerate -m "describe your change"
```

**Migration versions:**

| Version | Description |
|---------|-------------|
| `2026_06_17_0001` | Initial schema — all 10 tables |
| `2026_06_17_0002` | Add `is_active` to patients (soft delete support) |
| `2026_06_18_0003` | Add refresh token fields to healthcare_workers |

---

## Testing

```bash
# Run all tests
pytest

# Run with coverage report
pytest --cov=app --cov-report=term-missing

# Run a specific test file
pytest tests/test_auth.py -v

# Run tests in parallel
pytest -n auto
```

Test configuration is in `pytest.ini`. Tests use an async HTTP client (`httpx`) against the FastAPI test client.

---

## Docker Deployment

### Build and run with Docker Compose

```bash
# Development
docker-compose -f docker/docker-compose-dev.yml up --build

# Production
docker-compose -f docker/docker-compose-prod.yml up --build -d
```

### Build the image manually

```bash
docker build -t diabobesity-backend:latest .

docker run -p 8000:8000 \
  --env-file .env \
  -v /path/to/model/data:/app/model_data \
  diabobesity-backend:latest
```

The Dockerfile uses a **multi-stage build**:

- **Stage 1 (builder):** installs all Python dependencies (compiles C extensions for CatBoost, psycopg2, etc.)
- **Stage 2 (runtime):** copies only the compiled packages into a lean `python:3.11-slim` image, runs as a non-root user (`appuser`)

A `HEALTHCHECK` is configured — Docker will poll `GET /health` every 30 seconds and restart the container if it becomes unhealthy.

---

## Middleware

The following middleware is active on every request (outermost to innermost):

| Middleware | Purpose |
|------------|---------|
| `CORSMiddleware` | Handles OPTIONS preflight requests; allows listed origins |
| `log_requests` | Logs method, path, client IP, and user agent for every request |
| `add_request_id` | Attaches a `X-Request-ID` header for distributed tracing |

> **Ordering note:** `CORSMiddleware` is registered last (`app.add_middleware`) so that Starlette places it outermost in the middleware stack. This ensures CORS preflight (OPTIONS) requests are answered immediately before touching any application logic.

---

## Logging

The application uses Python's structured logging with two separate loggers:

- **Application logger** — logs all request events, startup messages, errors, and ML inference steps to `logs/app.log` and stdout
- **Audit logger** — writes a separate, immutable audit record for every login attempt, patient creation, prediction, and report generation — used for clinical compliance

Log level is controlled by the `LOG_LEVEL` environment variable (`DEBUG`, `INFO`, `WARNING`, `ERROR`).

---

## Security

| Concern | Implementation |
|---------|---------------|
| Passwords | Hashed with bcrypt (`BCRYPT_ROUNDS=12`); never stored in plain text |
| Access tokens | JWT signed with HS256; expire after 60 minutes |
| Refresh tokens | Stored as hashed values in the database; expire after 7 days |
| CORS | Explicit origin allowlist — no wildcard in production |
| SQL injection | All queries use SQLAlchemy ORM parameterised statements |
| Docker | Runs as non-root user (`appuser`, UID 1001) |
| Secrets | All secrets loaded from environment variables; never hardcoded |

---

## API Documentation

When running in development (`DEBUG=true`), auto-generated API docs are available at:

- **Swagger UI:** `http://localhost:8000/docs`
- **ReDoc:** `http://localhost:8000/redoc`
- **OpenAPI JSON:** `http://localhost:8000/openapi.json`

These are disabled in production (`DEBUG=false`) for security.
