"""
Pytest configuration and fixtures for testing.
"""

import asyncio
import os
import sys
import pytest
import pytest_asyncio
from typing import AsyncGenerator, Dict, Any
from datetime import datetime, timedelta, timezone

# ── CRITICAL: Override environment before importing app ──────────────────────
# This must happen BEFORE any app imports
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///:memory:"
os.environ["ENVIRONMENT"] = "testing"
os.environ["SECRET_KEY"] = "test_secret_key_for_testing_only"
os.environ["LOG_LEVEL"] = "DEBUG"

from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import StaticPool

# Add the app directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# ── Import app modules ──────────────────────────────────────────────────────
from app.core.database import Base, get_db_session
from app.core.security import hash_password, create_access_token

# Import all models to register them with Base.metadata
from app.models import (
    HealthcareWorker,
    Patient,
    ScreeningVisit,
    ScreeningData,
    Prediction,
    Recommendation,
    AuditLog,
    SHAPExplanation,
    ClinicalNote,
    Report,
)

# Import the FastAPI app instance
from app.main import app as fastapi_app

# ── Test Database Setup ──────────────────────────────────────────────────────

# Use in-memory SQLite for testing
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

# Create test engine with StaticPool to reuse the same connection
test_engine = create_async_engine(
    TEST_DATABASE_URL,
    echo=False,
    poolclass=StaticPool,
)

# Create test session maker
TestingSessionLocal = async_sessionmaker(
    test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


# ── Override the database initialization function ────────────────────────────

# Store original init_database
original_init = None

async def mock_init_database():
    """Mock database initialization for testing."""
    print("[setup] Mock database initialization - using SQLite in-memory")
    # Set the global engine and session maker to use test ones
    import app.core.database as db_module
    db_module._engine = test_engine
    db_module._async_session_maker = TestingSessionLocal

# Apply the mock
import app.main
app.main.init_database = mock_init_database


# ── Database initialization ──────────────────────────────────────────────────

async def init_test_db():
    """Initialize the test database."""
    print("\n[setup] Creating test database tables...")
    print(f"[setup] Tables registered: {list(Base.metadata.tables.keys())}")
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("[setup] Test database initialized!")


# ── Dependency Override ──────────────────────────────────────────────────────

async def override_get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """Override the database session dependency for testing."""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    async with TestingSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


# Apply override to the FastAPI app
fastapi_app.dependency_overrides[get_db_session] = override_get_db_session


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture(scope="session")
def event_loop():
    """Create an event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="session", autouse=True)
async def setup_test_db():
    """Set up the test database once per session."""
    print("\n[setup] setup_test_db (session scope) running...")
    await init_test_db()
    yield
    # Drop tables after all tests
    print("\n[setup] Dropping test database tables...")
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    print("[setup] Tables dropped!")


@pytest_asyncio.fixture
async def test_session() -> AsyncGenerator[AsyncSession, None]:
    """Provide a test database session."""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    async with TestingSessionLocal() as session:
        yield session
        await session.rollback()


@pytest.fixture
def test_client() -> TestClient:
    """Provide a test client for API tests."""
    with TestClient(fastapi_app) as client:
        yield client


@pytest_asyncio.fixture
async def test_db(test_session: AsyncSession):
    """Alias for test_session."""
    yield test_session


@pytest_asyncio.fixture
async def test_user(test_session: AsyncSession) -> HealthcareWorker:
    """Create a test healthcare worker."""
    worker = HealthcareWorker(
        full_name="Dr. Test User",
        email="test@example.com",
        password_hash=hash_password("TestPassword123!"),
        clinic_name="Test Clinic",
        is_active=True,
        is_verified=True,
    )
    test_session.add(worker)
    await test_session.commit()
    await test_session.refresh(worker)
    return worker


@pytest_asyncio.fixture
async def test_patient(test_session: AsyncSession, test_user: HealthcareWorker) -> Patient:
    """Create a test patient."""
    patient = Patient(
        full_name="John Test Doe",
        date_of_birth=datetime.strptime("1990-01-15", "%Y-%m-%d").date(),
        sex="Male",
        worker_id=test_user.worker_id,
        contact_info="+1234567890",
        national_id="TEST12345678",
        is_active=True,
    )
    test_session.add(patient)
    await test_session.commit()
    await test_session.refresh(patient)
    return patient


@pytest_asyncio.fixture
async def test_screening_data(
    test_session: AsyncSession,
    test_patient: Patient,
) -> Dict[str, Any]:
    """Create test screening data."""
    # Create visit
    visit = ScreeningVisit(
        patient_id=test_patient.patient_id,
        visit_date=datetime.now(timezone.utc),
        notes="Test screening visit",
    )
    test_session.add(visit)
    await test_session.flush()
    
    # Create screening data
    screening = ScreeningData(
        visit_id=visit.visit_id,
        weight=75.5,
        height=1.75,
        bmi=24.65,
        bmi_category="Normal",
        physical_activity=True,
        family_history_diabetes=True,
        previous_gdm=False,
        has_hypertension=False,
        is_pregnant=False,
        residence="Urban",
        age=35,
    )
    test_session.add(screening)
    await test_session.commit()
    await test_session.refresh(visit)
    await test_session.refresh(screening)
    
    return {
        "visit": visit,
        "screening": screening,
        "patient": test_patient,
    }


@pytest_asyncio.fixture
async def test_prediction(
    test_session: AsyncSession,
    test_screening_data: Dict[str, Any],
) -> Prediction:
    """Create a test prediction."""
    visit = test_screening_data["visit"]

    prediction = Prediction(
        visit_id=visit.visit_id,
        diabetes_probability=0.45,
        diabetes_risk_class="Moderate",
        diabetes_class="Prediabetes",
        obesity_probability=0.10,
        obesity_risk_class="Low",
        obesity_class="Normal",
        model_version="1.0.0",
        prediction_date=datetime.now(timezone.utc),
        latency_ms=125.5,
    )
    test_session.add(prediction)
    await test_session.commit()
    await test_session.refresh(prediction)

    return prediction


@pytest_asyncio.fixture
async def test_report(
    test_session: AsyncSession,
    test_screening_data: Dict[str, Any],
    test_user: HealthcareWorker,
) -> Report:
    """Create a test report metadata row for GET /reports/{id}."""
    visit = test_screening_data["visit"]

    report = Report(
        visit_id=visit.visit_id,
        generated_by=test_user.worker_id,
        format="PDF",
        file_path="reports/test/report.pdf",
        file_size_bytes="1024",
        generated_at=datetime.now(timezone.utc),
        downloaded_at=None,
        download_count="0",
        checksum=None,
    )

    test_session.add(report)
    await test_session.commit()
    await test_session.refresh(report)
    return report



@pytest.fixture
def test_auth_headers(test_user: HealthcareWorker) -> Dict[str, str]:
    """Create authentication headers for API tests."""
    access_token = create_access_token(
        data={
            "sub": test_user.worker_id,
            "worker_id": test_user.worker_id,
            "email": test_user.email,
        }
    )
    return {"Authorization": f"Bearer {access_token}"}


@pytest.fixture

def test_patient_data() -> Dict[str, Any]:
    """Test patient registration data."""
    return {
        "full_name": "Jane Smith",
        "date_of_birth": "1985-06-20",
        "sex": "Female",
        "contact_info": "+9876543210",
        "national_id": "TEST87654321",
    }


@pytest_asyncio.fixture
async def test_clinical_note(
    test_session: AsyncSession,
    test_patient: Patient,
    test_user: HealthcareWorker,
) -> "ClinicalNote":
    """Create a test clinical note for GET /api/v1/notes/{note_id}."""
    from app.models.clinical_note import ClinicalNote

    note = ClinicalNote(
        patient_id=test_patient.patient_id,
        author_id=test_user.worker_id,
        title="Test Note",
        content="This is a test clinical note.",
        note_type="GENERAL",
        is_urgent="NO",
    )

    test_session.add(note)
    await test_session.commit()
    await test_session.refresh(note)
    return note



@pytest.fixture
def test_screening_data_request() -> Dict[str, Any]:
    """Test screening data request."""
    return {
        "weight": 68.0,
        "height": 1.65,
        "physical_activity": True,
        "family_history_diabetes": False,
        "previous_gdm": True,
        "has_hypertension": False,
        "is_pregnant": False,
        "residence": "Urban",
        "notes": "Patient reports occasional headaches",
    }


@pytest.fixture
def test_login_data() -> Dict[str, str]:
    """Test login credentials."""
    return {
        "email": "test@example.com",
        "password": "TestPassword123!",
    }


@pytest.fixture
def test_invalid_login_data() -> Dict[str, str]:
    """Invalid test login credentials."""
    return {
        "email": "wrong@example.com",
        "password": "WrongPassword123!",
    }


@pytest.fixture
def test_register_data() -> Dict[str, Any]:
    """Test registration data."""
    return {
        "full_name": "Dr. New User",
        "email": "newuser@example.com",
        "password": "SecurePass456!",
        "clinic_name": "New Clinic",
    }


# Service fixtures
@pytest.fixture
def test_auth_service(test_session):
    """Provide auth service for testing."""
    from app.services.auth_service import AuthService
    return AuthService(test_session)


@pytest.fixture
def test_patient_service(test_session):
    """Provide patient service for testing."""
    from app.services.patient_service import PatientService
    return PatientService(test_session)


@pytest.fixture
def test_screening_service(test_session):
    """Provide screening service for testing."""
    from app.services.screening_service import ScreeningService
    return ScreeningService(test_session)