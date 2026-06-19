"""
Clinical notes endpoint tests.
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.clinical_note import ClinicalNote


class TestClinicalNoteEndpoints:
    """Test clinical note endpoints."""
    
    def test_create_note(
        self,
        test_client: TestClient,
        test_auth_headers: dict,
        test_patient
    ):
        """Test creating a clinical note."""
        note_data = {
            "title": "Test Note",
            "content": "This is a test clinical note.",
            "note_type": "GENERAL",
            "is_urgent": "NO",
        }
        
        response = test_client.post(
            f"/api/v1/notes/?patient_id={test_patient.patient_id}",
            json=note_data,
            headers=test_auth_headers
        )
        assert response.status_code == 201
        
        data = response.json()
        assert data["title"] == note_data["title"]
        assert data["content"] == note_data["content"]
        assert data["note_type"] == note_data["note_type"]
        assert data["is_urgent"] == note_data["is_urgent"]
        assert "note_id" in data
    
    def test_create_note_with_visit(
        self,
        test_client: TestClient,
        test_auth_headers: dict,
        test_patient,
        test_screening_data: dict
    ):
        """Test creating a clinical note with visit association."""
        visit = test_screening_data["visit"]
        
        note_data = {
            "title": "Visit Note",
            "content": "Patient presented with symptoms.",
            "note_type": "FOLLOW_UP",
            "is_urgent": "NO",
        }
        
        response = test_client.post(
            f"/api/v1/notes/?patient_id={test_patient.patient_id}&visit_id={visit.visit_id}",
            json=note_data,
            headers=test_auth_headers
        )
        assert response.status_code == 201
        
        data = response.json()
        assert data["visit_id"] == visit.visit_id
    
    def test_get_note(
        self,
        test_client: TestClient,
        test_auth_headers: dict,
        test_clinical_note: ClinicalNote
    ):
        """Test getting a clinical note."""
        response = test_client.get(
            f"/api/v1/notes/{test_clinical_note.note_id}",
            headers=test_auth_headers
        )
        assert response.status_code == 200
        
        data = response.json()
        assert data["note_id"] == test_clinical_note.note_id
        assert data["content"] == test_clinical_note.content
    
    def test_get_patient_notes(
        self,
        test_client: TestClient,
        test_auth_headers: dict,
        test_patient,
        test_clinical_note: ClinicalNote
    ):
        """Test getting all notes for a patient."""
        response = test_client.get(
            f"/api/v1/notes/patients/{test_patient.patient_id}",
            headers=test_auth_headers
        )
        assert response.status_code == 200
        
        data = response.json()
        assert "items" in data
        assert len(data["items"]) > 0
        assert data["pagination"]["page"] == 1
    
    def test_get_urgent_notes(
        self,
        test_client: TestClient,
        test_auth_headers: dict
    ):
        """Test getting urgent notes."""
        response = test_client.get(
            "/api/v1/notes/urgent",
            headers=test_auth_headers
        )
        assert response.status_code == 200
        
        data = response.json()
        assert "items" in data
        assert "pagination" in data
    
    def test_update_note(
        self,
        test_client: TestClient,
        test_auth_headers: dict,
        test_clinical_note: ClinicalNote
    ):
        """Test updating a clinical note."""
        update_data = {
            "title": "Updated Title",
            "content": "Updated content.",
            "is_urgent": "YES",
        }
        
        response = test_client.patch(
            f"/api/v1/notes/{test_clinical_note.note_id}",
            json=update_data,
            headers=test_auth_headers
        )
        assert response.status_code == 200
        
        data = response.json()
        assert data["title"] == update_data["title"]
        assert data["content"] == update_data["content"]
        assert data["is_urgent"] == update_data["is_urgent"]
    
    def test_delete_note(
        self,
        test_client: TestClient,
        test_auth_headers: dict,
        test_clinical_note: ClinicalNote
    ):
        """Test deleting a clinical note."""
        response = test_client.delete(
            f"/api/v1/notes/{test_clinical_note.note_id}",
            headers=test_auth_headers
        )
        assert response.status_code == 200
        assert response.json()["success"] is True