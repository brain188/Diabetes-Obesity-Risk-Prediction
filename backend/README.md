# Intelligent DSS for Early Risk Prediction of Type 2 Diabetes and Obesity

[![CI/CD Pipeline](https://github.com/yourusername/dss-backend/actions/workflows/ci.yml/badge.svg)](https://github.com/yourusername/dss-backend/actions/workflows/ci.yml)
[![codecov](https://codecov.io/gh/yourusername/dss-backend/branch/main/graph/badge.svg)](https://codecov.io/gh/yourusername/dss-backend)
[![Docker Pulls](https://img.shields.io/docker/pulls/yourusername/dss-backend)](https://hub.docker.com/r/yourusername/dss-backend)
[![Python Version](https://img.shields.io/badge/python-3.11-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104.1-009688.svg)](https://fastapi.tiangolo.com/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

## 📋 Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Architecture](#architecture)
- [Technology Stack](#technology-stack)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Configuration](#configuration)
- [Running the Application](#running-the-application)
- [API Documentation](#api-documentation)
- [Database Migrations](#database-migrations)
- [Testing](#testing)
- [Docker Deployment](#docker-deployment)
- [Project Structure](#project-structure)
- [Contributing](#contributing)
- [License](#license)

## 🎯 Overview

The Intelligent Decision Support System (DSS) is a production-ready backend application designed for early risk prediction of Type 2 Diabetes (T2D) and obesity in low-resource healthcare settings. It leverages machine learning to provide healthcare workers with actionable risk assessments, explanations, and clinical recommendations.

### Key Objectives

- **Early Detection**: Identify patients at risk of T2D and obesity
- **Explainable AI**: Provide SHAP-based explanations for predictions
- **Low-Resource Friendly**: Designed for use in settings with limited resources
- **Clinical Integration**: Generate actionable recommendations for healthcare workers

## ✨ Features

### Core Functionality

- ✅ **User Authentication**: Secure JWT-based authentication with role management
- ✅ **Patient Management**: Register, search, and manage patient records
- ✅ **Screening Data Capture**: Structured data entry with validation
- ✅ **Dual Risk Prediction**: Diabetes (ML) and Obesity (rule-based) assessment
- ✅ **Explainable AI**: SHAP and LIME explanations for predictions
- ✅ **Clinical Recommendations**: Automated, risk-based guidance
- ✅ **Report Generation**: PDF reports with patient data and predictions
- ✅ **Clinical Notes**: Free-text documentation
- ✅ **Audit Logging**: Comprehensive audit trail for compliance

### Technical Features

- ✅ Async/await throughout for high performance
- ✅ PostgreSQL with async SQLAlchemy
- ✅ Redis caching (optional)
- ✅ Comprehensive test suite with 80%+ coverage
- ✅ Docker containerization with multi-stage builds
- ✅ CI/CD pipeline with GitHub Actions
- ✅ OpenAPI/Swagger documentation
- ✅ Production-ready logging and monitoring

## 🏗️ Architecture

┌─────────────────────────────────────────────────────────────────────────────┐
│ Client (Web/Mobile) │
└─────────────────────────────────────────────────────────────────────────────┘
│
▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ Nginx (Reverse Proxy) │
│ - Rate Limiting / SSL Termination │
└─────────────────────────────────────────────────────────────────────────────┘
│
▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ FastAPI Application │
│ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────────────┐ │
│ │ API v1 │ │ Services │ │ Repositories│ │ ML Module │ │
│ │ Routes │ │ (Business │ │ (Database │ │ - Model Loading │ │
│ │ - Auth │ │ Logic) │ │ Access) │ │ - Prediction │ │
│ │ - Patients │ │ - Auth │ │ - CRUD │ │ - SHAP Explanations│ │
│ │ - Screening│ │ - Patient │ │ - Queries │ │ - Feature Import. │ │
│ │ - Predict. │ │ - Screening│ │ - Filters │ │ │ │
│ │ - Reports │ │ - Predict. │ │ │ │ │ │
│ │ - Notes │ │ - Report │ │ │ │ │ │
│ └─────────────┘ └─────────────┘ └─────────────┘ └─────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────┘
│
┌───────────────────────┼───────────────────────┐
│ │ │
▼ ▼ ▼
┌─────────────────┐ ┌─────────────────┐ ┌─────────────────────────┐
│ PostgreSQL │ │ Redis │ │ Model Artifacts │
│ (Database) │ │ (Cache) │ │ (CatBoost Models) │
└─────────────────┘ └─────────────────┘ └─────────────────────────┘


## 🛠️ Technology Stack

| Component | Technology | Version |
|-----------|------------|---------|
| **Framework** | FastAPI | 0.104.1 |
| **ORM** | SQLAlchemy | 2.0.23 |
| **Database** | PostgreSQL | 15 |
| **Cache** | Redis | 7 |
| **ML** | CatBoost, SHAP, scikit-learn | Latest |
| **Auth** | JWT (python-jose) | 3.3.0 |
| **Testing** | pytest | 7.4.3 |
| **Container** | Docker | 24+ |
| **CI/CD** | GitHub Actions | Latest |
| **Monitoring** | Prometheus, Grafana (optional) | Latest |

## 📋 Prerequisites

- **Python**: 3.10 or higher
- **PostgreSQL**: 15 or higher
- **Redis**: 7 or higher (optional)
- **Docker**: 24+ (for containerized deployment)
- **Git**: 2.30+ (for version control)

## 🚀 Installation

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/dss-backend.git
cd dss-backend

### 2. Create Virtual Environment

python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

### 3. Install Dependencies

pip install --upgrade pip
pip install -r requirements.txt

### 3. Run Application

# Development mode (with auto-reload)
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Production mode
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4


## Project Structure

backend/
├── app/
│   ├── __init__.py
│   ├── main.py                      # FastAPI application entry point
│   ├── api/
│   │   └── v1/                      # API version 1 routes
│   │       ├── auth.py              # Authentication endpoints
│   │       ├── patients.py          # Patient endpoints
│   │       ├── screening.py         # Screening endpoints
│   │       ├── prediction.py        # Prediction endpoints
│   │       ├── reports.py           # Report endpoints
│   │       ├── notes.py             # Clinical notes endpoints
│   │       └── analytics.py         # Analytics endpoints
│   ├── core/
│   │   ├── config.py                # Application configuration
│   │   ├── constants.py             # Application constants
│   │   ├── database.py              # Database connection
│   │   ├── security.py              # Authentication utilities
│   │   ├── logging.py               # Logging configuration
│   │   ├── exceptions.py            # Custom exceptions
│   │   └── dependencies.py          # FastAPI dependencies
│   ├── models/                      # SQLAlchemy ORM models
│   ├── schemas/                     # Pydantic schemas
│   ├── repositories/                # Database access layer
│   ├── services/                    # Business logic layer
│   ├── ml/                          # ML model loading and prediction
│   └── utils/                       # Utility functions
├── tests/                           # Test suite
├── alembic/                         # Database migrations
├── docker/                          # Docker configuration
├── scripts/                         # Utility scripts
├── requirements.txt                 # Production dependencies
├── requirements-dev.txt             # Development dependencies
├── Dockerfile                       # Docker build file
├── docker-compose.yml               # Docker Compose configuration
├── .env.example                     # Environment variables example
├── .github/workflows/ci.yml         # CI/CD pipeline
├── Makefile                         # Common commands
└── README.md                        # This file