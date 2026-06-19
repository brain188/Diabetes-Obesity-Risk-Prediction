"""
Patient endpoint tests.
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.patient import Patient


class TestPatientEndpoints:
    """Test patient management endpoints."""
    
    def test_create_patient(
        self,
        test_client: TestClient,
        test_auth_headers: dict,
        test_patient_data: dict
    ):
        """Test creating a new patient."""
        response = test_client.post(
            "/api/v1/patients/",
            json=test_patient_data,
            headers=test_auth_headers
        )
        assert response.status_code == 201
        
        data = response.json()
        assert data["full_name"] == test_patient_data["full_name"]
        assert data["sex"] == test_patient_data["sex"]
        assert data["contact_info"] == test_patient_data["contact_info"]
        assert data["national_id"] == test_patient_data["national_id"]
        assert "patient_id" in data
        assert data["age"] is not None
    
    def test_create_patient_duplicate_national_id(
        self,
        test_client: TestClient,
        test_auth_headers: dict,
        test_patient_data: dict,
        test_patient: Patient
    ):
        """Test creating patient with duplicate national ID."""
        test_patient_data["national_id"] = test_patient.national_id
        response = test_client.post(
            "/api/v1/patients/",
            json=test_patient_data,
            headers=test_auth_headers
        )
        assert response.status_code == 409
        assert "DUPLICATE_RESOURCE" in response.json()["error"]
    
    def test_get_patient(
        self,
        test_client: TestClient,
        test_auth_headers: dict,
        test_patient: Patient
    ):
        """Test getting a patient by ID."""
        response = test_client.get(
            f"/api/v1/patients/{test_patient.patient_id}",
            headers=test_auth_headers
        )
        assert response.status_code == 200
        
        data = response.json()
        assert data["patient_id"] == test_patient.patient_id
        assert data["full_name"] == test_patient.full_name
        assert data["sex"] == test_patient.sex
        assert data["age"] is not None
    
    def test_get_patient_not_found(
        self,
        test_client: TestClient,
        test_auth_headers: dict
    ):
        """Test getting a non-existent patient."""
        response = test_client.get(
            "/api/v1/patients/non-existent-id",
            headers=test_auth_headers
        )
        assert response.status_code == 404
        assert "RESOURCE_NOT_FOUND" in response.json()["error"]
    
    def test_update_patient(
        self,
        test_client: TestClient,
        test_auth_headers: dict,
        test_patient: Patient
    ):
        """Test updating a patient."""
        update_data = {
            "full_name": "Updated Name",
            "contact_info": "+1111111111",
        }
        response = test_client.patch(
            f"/api/v1/patients/{test_patient.patient_id}",
            json=update_data,
            headers=test_auth_headers
        )
        assert response.status_code == 200
        
        data = response.json()
        assert data["full_name"] == update_data["full_name"]
        assert data["contact_info"] == update_data["contact_info"]
    
    def test_search_patients(
        self,
        test_client: TestClient,
        test_auth_headers: dict,
        test_patient: Patient
    ):
        """Test searching for patients."""
        response = test_client.get(
            f"/api/v1/patients/search?query={test_patient.full_name[:3]}",
            headers=test_auth_headers
        )
        assert response.status_code == 200
        
        data = response.json()
        assert "items" in data
        assert len(data["items"]) > 0
        assert data["page"] == 1
        assert data["page_size"] == 20
    
    def test_list_patients(
        self,
        test_client: TestClient,
        test_auth_headers: dict
    ):
        """Test listing all patients."""
        response = test_client.get(
            "/api/v1/patients/",
            headers=test_auth_headers
        )
        assert response.status_code == 200
        
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert data["page"] == 1
    
    def test_get_patient_summary(
        self,
        test_client: TestClient,
        test_auth_headers: dict,
        test_patient: Patient
    ):
        """Test getting patient summary."""
        response = test_client.get(
            f"/api/v1/patients/{test_patient.patient_id}/summary",
            headers=test_auth_headers
        )
        assert response.status_code == 200
        
        data = response.json()
        assert data["patient_id"] == test_patient.patient_id
        assert data["full_name"] == test_patient.full_name
        assert "total_visits" in data
        assert "registered_at" in data
    
    def test_delete_patient(
        self,
        test_client: TestClient,
        test_auth_headers: dict,
        test_patient: Patient
    ):
        """Test deleting a patient."""
        response = test_client.delete(
            f"/api/v1/patients/{test_patient.patient_id}",
            headers=test_auth_headers
        )
        assert response.status_code == 200
        assert response.json()["success"] is True