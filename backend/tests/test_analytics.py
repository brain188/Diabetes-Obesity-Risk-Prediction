"""
Analytics endpoint tests.
"""

import pytest
from fastapi.testclient import TestClient


class TestAnalyticsEndpoints:
    """Test analytics and feature importance endpoints."""
    
    def test_get_feature_importance(
        self,
        test_client: TestClient,
        test_auth_headers: dict
    ):
        """Test getting global feature importance."""
        response = test_client.get(
            "/api/v1/analytics/feature-importance",
            headers=test_auth_headers
        )
        
        # If model not loaded, test might fail
        if response.status_code == 503:
            assert "MODEL_NOT_LOADED" in response.json()["error"]
        else:
            assert response.status_code == 200
            data = response.json()
            assert "model_version" in data
            assert "feature_importance" in data
            assert isinstance(data["feature_importance"], dict)
            assert "sorted_features" in data
    
    def test_get_model_info(
        self,
        test_client: TestClient,
        test_auth_headers: dict
    ):
        """Test getting model information."""
        response = test_client.get(
            "/api/v1/analytics/model/info",
            headers=test_auth_headers
        )
        
        # If model not loaded, test might fail
        if response.status_code == 503:
            assert "MODEL_NOT_LOADED" in response.json()["error"]
        else:
            assert response.status_code == 200
            data = response.json()
            assert "model_name" in data
            assert "model_version" in data
            assert "feature_names" in data
            assert "is_loaded" in data
    
    def test_get_audit_summary(
        self,
        test_client: TestClient,
        test_auth_headers: dict
    ):
        """Test getting audit summary."""
        response = test_client.get(
            "/api/v1/analytics/audit/summary?days=7",
            headers=test_auth_headers
        )
        assert response.status_code == 200
        
        data = response.json()
        assert "period_days" in data
        assert "start_date" in data
        assert "event_counts" in data
        assert "total_events" in data
    
    def test_get_recent_activities(
        self,
        test_client: TestClient,
        test_auth_headers: dict
    ):
        """Test getting recent activities."""
        response = test_client.get(
            "/api/v1/analytics/audit/activities?limit=10",
            headers=test_auth_headers
        )
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)
    
    def test_get_dashboard_stats(
        self,
        test_client: TestClient,
        test_auth_headers: dict
    ):
        """Test getting dashboard statistics."""
        response = test_client.get(
            "/api/v1/analytics/stats/dashboard",
            headers=test_auth_headers
        )
        assert response.status_code == 200
        
        data = response.json()
        assert "total_patients" in data
        assert "total_screenings" in data
        assert "risk_distribution" in data
        assert "recent_activities" in data