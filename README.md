# DiabObesity — Intelligent Clinical Decision Support System

[![FastAPI](https://img.shields.io/badge/Backend-FastAPI-009688)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/Frontend-React_19-61DAFB)](https://react.dev/)
[![CatBoost](https://img.shields.io/badge/ML_Model-CatBoost-yellow)](https://catboost.ai/)
[![Kedro](https://img.shields.io/badge/ML_Pipeline-Kedro_1.4-ffc900)](https://kedro.org/)
[![PostgreSQL](https://img.shields.io/badge/Database-PostgreSQL_15-336791)](https://www.postgresql.org/)

---

## Overview

**DiabObesity** is a full-stack Intelligent Decision Support System (DSS) for early risk prediction of Type 2 Diabetes and obesity in low-resource clinical settings. Healthcare workers enter patient screening data through a React web interface; the system runs it through a trained CatBoost machine learning model and returns a risk classification, probability scores, SHAP/LIME explanations, and clinical recommendations — all in real time.

The system is designed to assist, not replace, clinical judgement. Every prediction is accompanied by an explainability report showing which features drove the result, allowing clinicians to understand and trust the output.

---

## System Architecture

![Full System Architecture](full_architecture/full%20architecture%20diagram.png)

---

## Repository Structure

```
DiabObesity/
├── frontend/
│   └── Intelligent_DSS/        # React 19 + Vite + TypeScript + Tailwind CSS
├── backend/                    # FastAPI REST API + SQLAlchemy + Alembic
├── model/
│   └── diabobesity-prediction/ # Kedro ML pipeline (training, evaluation, inference)
└── full_architecture/          # System architecture diagram
```

---

## Technology Stack

| Layer | Technology |
|-------|-----------|
| **Frontend** | React 19, TypeScript, Vite 8, Tailwind CSS 4, shadcn/ui, Zustand, TanStack Query, React Router v7, Recharts, Axios |
| **Backend** | Python 3.11, FastAPI, SQLAlchemy 2.0 (async), asyncpg, Pydantic v2, Alembic, python-jose (JWT), bcrypt, ReportLab |
| **Database** | PostgreSQL 15 via Supabase (connection-pooled with PgBouncer) |
| **ML Model** | CatBoost v1.0.0 (selected from 5 candidates), SHAP TreeExplainer, LIME, scikit-learn, SMOTE |
| **ML Pipeline** | Kedro 1.4, MLflow 2.18, Optuna (hyperparameter tuning), pandas, NumPy |
| **Infrastructure** | Docker (multi-stage build), Docker Compose, Nginx |

---

## ML Model Summary

The diabetes risk model is a **3-class CatBoost classifier** trained and managed with Kedro.

| Property | Value |
|----------|-------|
| Task | Normal / Prediabetes / Diabetic classification |
| Training records | 10,000 |
| Test records | 2,000 |
| Input features | 10 clinical features |
| Test accuracy | 73.05% |
| ROC-AUC (one-vs-rest) | 84.54% |
| Explainability | SHAP waterfall + LIME per prediction |

**Risk bands** (Youden-J optimised threshold):

| Band | Condition |
|------|-----------|
| Low | P(Diabetic) < 0.347 |
| Moderate | 0.347 ≤ P(Diabetic) < 0.547 |
| High | P(Diabetic) ≥ 0.547 |

See [`model/diabobesity-prediction/README.md`](model/diabobesity-prediction/README.md) for full pipeline and evaluation details.

---

## Getting Started

### Prerequisites

- Python 3.11+
- Node.js 18+
- PostgreSQL 15 (or a Supabase project)
- ML artifacts from the Kedro model (run the Kedro pipeline first or obtain pre-built artifacts)

---

### 1. ML Model — Train and generate artifacts

```bash
cd model/diabobesity-prediction
pip install -r requirements.txt
kedro run          # runs data_processing → feature_engineering → training → evaluation
```

Artifacts are written to `model/diabobesity-prediction/data/06_models/` and `data/08_reporting/`.

---

### 2. Backend — FastAPI API server

```bash
cd backend

# Create and activate virtual environment
python -m venv .venv
.venv\Scripts\activate        # Windows
source .venv/bin/activate     # Linux/macOS

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env          # then fill in DATABASE_URL and SECRET_KEY

# Apply database migrations
alembic upgrade head

# Start the server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

API available at `http://localhost:8000`  
Swagger docs at `http://localhost:8000/docs` (when `DEBUG=true`)

See [`backend/README.md`](backend/README.md) for full configuration and API reference.

---

### 3. Frontend — React web application

```bash
cd frontend/Intelligent_DSS

# Install dependencies
npm install

# Configure environment
echo "VITE_API_URL=http://localhost:8000/api/v1" > .env

# Start the development server
npm run dev
```

Application available at `http://localhost:5173`

---

## Key Features

**For healthcare workers:**

- Register and manage patient records
- Enter structured screening data (BMI, family history, pregnancy status, etc.)
- View real-time diabetes risk predictions with probability scores
- Read SHAP and LIME explanations showing which features drove the prediction
- Generate and download PDF clinical reports
- Write and retrieve clinical notes per patient
- View analytics dashboard with risk distributions, trends, and model performance

**For system administrators:**

- Manage user accounts and roles
- Review audit logs of all clinical actions
- Monitor system health and model readiness

---

## API Overview

The backend exposes a versioned REST API at `/api/v1`:

| Router | Prefix | Purpose |
|--------|--------|---------|
| Auth | `/auth` | Login, register, JWT refresh, password management |
| Patients | `/patients` | Patient CRUD, search, soft delete |
| Screening | `/screening` | Screening visit and data entry |
| Predictions | `/predictions` | Run ML prediction, fetch results and explanations |
| Reports | `/reports` | Generate and download PDF reports |
| Notes | `/notes` | Clinical free-text notes |
| Analytics | `/analytics` | Dashboard stats, risk distribution, model info, audit summary |

All endpoints require a Bearer JWT token except `/auth/login` and `/auth/register`.

---

## Docker Deployment

```bash
# Development
docker-compose -f backend/docker/docker-compose-dev.yml up --build

# Production
docker-compose -f backend/docker/docker-compose-prod.yml up --build -d
```

The backend Dockerfile uses a multi-stage build: a builder stage compiles all C extensions (CatBoost, psycopg2), and the final slim runtime image runs as a non-root user with a Docker health check configured.

---

## Project Documentation

| Component | README |
|-----------|--------|
| Full system | This file |
| Backend API | [`backend/README.md`](backend/README.md) |
| ML model & pipelines | [`model/diabobesity-prediction/README.md`](model/diabobesity-prediction/README.md) |
