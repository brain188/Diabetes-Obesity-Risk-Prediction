"""
Screening endpoint tests.
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.screening_data import ScreeningVisit, ScreeningData


class TestScreeningEndpoints:
    """Test screening endpoints."""
    
    def test_create_visit(
        self,
        test_client: TestClient,
        test_auth_headers: dict,
        test_patient
    ):
        """Test creating a screening visit."""
        response = test_client.post(
            f"/api/v1/screening/visits?patient_id={test_patient.patient_id}&notes=Test visit",
            headers=test_auth_headers
        )
        assert response.status_code == 201
        
        data = response.json()
        assert "visit_id" in data
        assert data["patient_id"] == test_patient.patient_id
        assert data["notes"] == "Test visit"
    
    def test_create_visit_patient_not_found(
        self,
        test_client: TestClient,
        test_auth_headers: dict
    ):
        """Test creating a visit for non-existent patient."""
        response = test_client.post(
            "/api/v1/screening/visits?patient_id=non-existent-id",
            headers=test_auth_headers
        )
        assert response.status_code == 404
        assert "RESOURCE_NOT_FOUND" in response.json()["error"]
    
    def test_save_screening_data(
        self,
        test_client: TestClient,
        test_auth_headers: dict,
        test_screening_data_request: dict,
        test_patient
    ):
        """Test saving screening data."""
        # Create a fresh visit with no existing screening data
        visit_response = test_client.post(
            f"/api/v1/screening/visits?patient_id={test_patient.patient_id}",
            headers=test_auth_headers
        )
        assert visit_response.status_code == 201
        visit_id = visit_response.json()["visit_id"]
        
        response = test_client.post(
            f"/api/v1/screening/visits/{visit_id}/data",
            json=test_screening_data_request,
            headers=test_auth_headers
        )
        assert response.status_code == 201
        
        data = response.json()
        assert data["visit_id"] == visit_id
        assert data["weight"] == test_screening_data_request["weight"]
        assert data["height"] == test_screening_data_request["height"]
        assert "bmi" in data
        assert "bmi_category" in data
        assert data["physical_activity"] == test_screening_data_request["physical_activity"]
    
    def test_get_visit(
        self,
        test_client: TestClient,
        test_auth_headers: dict,
        test_screening_data: dict
    ):
        """Test getting a screening visit."""
        visit = test_screening_data["visit"]
        
        response = test_client.get(
            f"/api/v1/screening/visits/{visit.visit_id}",
            headers=test_auth_headers
        )
        assert response.status_code == 200
        
        data = response.json()
        assert data["visit_id"] == visit.visit_id
        assert "screening_data" in data
        assert data["screening_data"]["bmi"] == test_screening_data["screening"].bmi
    
    def test_get_visit_not_found(
        self,
        test_client: TestClient,
        test_auth_headers: dict
    ):
        """Test getting a non-existent visit."""
        response = test_client.get(
            "/api/v1/screening/visits/non-existent-id",
            headers=test_auth_headers
        )
        assert response.status_code == 404
    
    def test_get_patient_visits(
        self,
        test_client: TestClient,
        test_auth_headers: dict,
        test_screening_data: dict,
        test_patient
    ):
        """Test getting all visits for a patient."""
        response = test_client.get(
            f"/api/v1/screening/patients/{test_patient.patient_id}/visits",
            headers=test_auth_headers
        )
        assert response.status_code == 200
        
        data = response.json()
        assert "items" in data
        assert data["page"] == 1
        assert len(data["items"]) > 0
    
    def test_get_latest_screening(
        self,
        test_client: TestClient,
        test_auth_headers: dict,
        test_patient,
        test_screening_data: dict
    ):
        """Test getting the latest screening data for a patient."""
        response = test_client.get(
            f"/api/v1/screening/patients/{test_patient.patient_id}/latest",
            headers=test_auth_headers
        )
        assert response.status_code == 200
        
        data = response.json()
        if data:
            assert "bmi" in data
            assert "bmi_category" in data
            assert "physical_activity" in data