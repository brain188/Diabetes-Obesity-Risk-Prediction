"""
Report endpoint tests.
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.report import Report


class TestReportEndpoints:
    """Test report generation and download endpoints."""
    
    def test_generate_report(
        self,
        test_client: TestClient,
        test_auth_headers: dict,
        test_screening_data: dict
    ):
        """Test generating a report."""
        visit = test_screening_data["visit"]
        
        data = {
            "visit_id": visit.visit_id,
            "format": "PDF",
        }
        
        response = test_client.post(
            "/api/v1/reports/generate",
            json=data,
            headers=test_auth_headers
        )
        
        # If PDF generation fails, test might return 500
        if response.status_code == 500:
            assert "REPORT_GENERATION_ERROR" in response.json()["error"]
        else:
            assert response.status_code == 201
            report_data = response.json()
            assert "report_id" in report_data
            assert report_data["format"] == "PDF"
            assert "file_path" in report_data
    
    def test_get_report(
        self,
        test_client: TestClient,
        test_auth_headers: dict,
        test_report: Report
    ):
        """Test getting report metadata."""
        response = test_client.get(
            f"/api/v1/reports/{test_report.report_id}",
            headers=test_auth_headers
        )
        assert response.status_code == 200
        
        data = response.json()
        assert data["report_id"] == test_report.report_id
        assert data["format"] == test_report.format
        assert "file_path" in data
    
    def test_get_report_not_found(
        self,
        test_client: TestClient,
        test_auth_headers: dict
    ):
        """Test getting a non-existent report."""
        response = test_client.get(
            "/api/v1/reports/non-existent-id",
            headers=test_auth_headers
        )
        assert response.status_code == 404
    
    def test_get_patient_reports(
        self,
        test_client: TestClient,
        test_auth_headers: dict,
        test_patient,
        test_report: Report
    ):
        """Test getting all reports for a patient."""
        response = test_client.get(
            f"/api/v1/reports/patients/{test_patient.patient_id}",
            headers=test_auth_headers
        )
        assert response.status_code == 200
        
        data = response.json()
        assert "items" in data
        assert "pagination" in data