#!/usr/bin/env python3
"""
Tests for export security and ALLOW_EXPORTS enforcement.

This module tests that ALLOW_EXPORTS=false is properly enforced server-side,
admin override functionality works correctly, and proper audit logging occurs.
"""

import os
import pytest
import jwt
from datetime import datetime, timedelta
from unittest.mock import patch
from fastapi.testclient import TestClient

import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'app'))

class TestExportSecurity:
    """Test export security enforcement and admin override functionality."""
    
    @pytest.fixture
    def setup_env(self):
        """Set up test environment variables."""
        # Backup original env vars
        original_env = {}
        env_vars = ['ALLOW_EXPORTS', 'SUPABASE_JWT_SECRET', 'ADMIN_EMAILS']
        for var in env_vars:
            if var in os.environ:
                original_env[var] = os.environ[var]
        
        # Set test values
        os.environ['SUPABASE_JWT_SECRET'] = 'test_jwt_secret_for_testing'
        os.environ['ADMIN_EMAILS'] = 'admin@test.com'
        
        yield
        
        # Restore environment
        for var in env_vars:
            if var in original_env:
                os.environ[var] = original_env[var]
            elif var in os.environ:
                del os.environ[var]
    
    @pytest.fixture
    def client(self, setup_env):
        """Create test client."""
        # Import after env setup to ensure proper configuration
        from main import app
        return TestClient(app)
    
    def create_jwt_token(self, user_id: str, email: str, role: str = "user") -> str:
        """Create a test JWT token."""
        payload = {
            "sub": user_id,
            "email": email,
            "aud": "authenticated",
            "iat": datetime.utcnow().timestamp(),
            "exp": (datetime.utcnow() + timedelta(hours=1)).timestamp(),
            "user_metadata": {"role": role}
        }
        return jwt.encode(payload, os.environ['SUPABASE_JWT_SECRET'], algorithm="HS256")
    
    def test_export_blocked_when_allow_exports_false_non_admin(self, client, setup_env):
        """Test that non-admin users get 403 when ALLOW_EXPORTS=false."""
        # Set ALLOW_EXPORTS=false
        os.environ['ALLOW_EXPORTS'] = 'false'
        
        # Create token for regular user
        token = self.create_jwt_token("user123", "user@test.com", "user")
        
        response = client.post(
            "/api/export/data",
            json={
                "export_type": "leads",
                "format": "csv"
            },
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 403
        assert "Export not allowed" in response.json()["detail"]
        assert "ALLOW_EXPORTS=false" in response.json()["detail"]
    
    def test_export_blocked_when_allow_exports_false_admin_no_override(self, client, setup_env):
        """Test that admin users get 403 when ALLOW_EXPORTS=false and no override requested."""
        # Set ALLOW_EXPORTS=false
        os.environ['ALLOW_EXPORTS'] = 'false'
        
        # Create token for admin user
        token = self.create_jwt_token("admin123", "admin@test.com", "admin")
        
        response = client.post(
            "/api/export/data",
            json={
                "export_type": "leads",
                "format": "csv",
                "admin_override": False  # Explicitly no override
            },
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 403
        assert "Export not allowed" in response.json()["detail"]
    
    def test_export_allowed_when_allow_exports_true(self, client, setup_env):
        """Test that exports work when ALLOW_EXPORTS=true."""
        # Set ALLOW_EXPORTS=true
        os.environ['ALLOW_EXPORTS'] = 'true'
        
        # Create token for regular user
        token = self.create_jwt_token("user123", "user@test.com", "user")
        
        response = client.post(
            "/api/export/data",
            json={
                "export_type": "leads",
                "format": "csv"
            },
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 200
        assert response.json()["message"] == "Export completed successfully"
        assert response.json()["export_type"] == "leads"
    
    def test_admin_override_allows_export_when_allow_exports_false(self, client, setup_env):
        """Test that admin override allows export when ALLOW_EXPORTS=false."""
        # Set ALLOW_EXPORTS=false
        os.environ['ALLOW_EXPORTS'] = 'false'
        
        # Create token for admin user
        token = self.create_jwt_token("admin123", "admin@test.com", "admin")
        
        response = client.post(
            "/api/export/data",
            json={
                "export_type": "leads",
                "format": "csv",
                "admin_override": True
            },
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 200
        assert response.json()["message"] == "Export completed successfully"
        assert response.json()["allowed_via"] == "admin_override"
    
    def test_non_admin_cannot_use_override(self, client, setup_env):
        """Test that non-admin users cannot use admin override."""
        # Set ALLOW_EXPORTS=false
        os.environ['ALLOW_EXPORTS'] = 'false'
        
        # Create token for regular user
        token = self.create_jwt_token("user123", "user@test.com", "user")
        
        response = client.post(
            "/api/export/data",
            json={
                "export_type": "leads",
                "format": "csv",
                "admin_override": True  # Non-admin trying to use override
            },
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 403
        assert "Admin privileges required for export override" in response.json()["detail"]
    
    def test_invalid_export_type_returns_400(self, client, setup_env):
        """Test that invalid export type returns 400."""
        # Set ALLOW_EXPORTS=true to focus on validation error
        os.environ['ALLOW_EXPORTS'] = 'true'
        
        token = self.create_jwt_token("user123", "user@test.com", "user")
        
        response = client.post(
            "/api/export/data",
            json={
                "export_type": "invalid_type",
                "format": "csv"
            },
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 400
        assert "Invalid export_type" in response.json()["detail"]
    
    def test_export_status_shows_admin_capabilities(self, client, setup_env):
        """Test that export status endpoint shows admin capabilities."""
        os.environ['ALLOW_EXPORTS'] = 'false'
        
        # Test for admin user
        admin_token = self.create_jwt_token("admin123", "admin@test.com", "admin")
        
        response = client.get(
            "/api/export/status",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        assert response.status_code == 200
        assert response.json()["user_is_admin"] is True
        assert response.json()["admin_override_available"] is True
        assert response.json()["exports_enabled"] is False
        
        # Test for regular user
        user_token = self.create_jwt_token("user123", "user@test.com", "user")
        
        response = client.get(
            "/api/export/status",
            headers={"Authorization": f"Bearer {user_token}"}
        )
        
        assert response.status_code == 200
        assert response.json()["user_is_admin"] is False
        assert response.json()["admin_override_available"] is False
    
    def test_unauthorized_request_returns_403(self, client, setup_env):
        """Test that requests without auth token return 403."""
        response = client.post(
            "/api/export/data",
            json={
                "export_type": "leads",
                "format": "csv"
            }
        )
        
        assert response.status_code == 403
        assert "Not authenticated" in response.json()["detail"]
    
    def test_invalid_jwt_token_returns_401(self, client, setup_env):
        """Test that invalid JWT token returns 401."""
        response = client.post(
            "/api/export/data",
            json={
                "export_type": "leads",
                "format": "csv"
            },
            headers={"Authorization": "Bearer invalid_token"}
        )
        
        assert response.status_code == 401


class TestAuditLogging:
    """Test that export attempts are properly audited."""
    
    @pytest.fixture
    def setup_env(self):
        """Set up test environment variables."""
        original_env = {}
        env_vars = ['ALLOW_EXPORTS', 'SUPABASE_JWT_SECRET']
        for var in env_vars:
            if var in os.environ:
                original_env[var] = os.environ[var]
        
        os.environ['SUPABASE_JWT_SECRET'] = 'test_jwt_secret_for_testing'
        
        yield
        
        for var in env_vars:
            if var in original_env:
                os.environ[var] = original_env[var]
            elif var in os.environ:
                del os.environ[var]
    
    def create_jwt_token(self, user_id: str, email: str, role: str = "user") -> str:
        """Create a test JWT token."""
        payload = {
            "sub": user_id,
            "email": email,
            "aud": "authenticated",
            "iat": datetime.utcnow().timestamp(),
            "exp": (datetime.utcnow() + timedelta(hours=1)).timestamp(),
            "user_metadata": {"role": role}
        }
# Shared utility function for creating JWT tokens for tests
def create_jwt_token(user_id: str, email: str, role: str = "user") -> str:
    """Create a test JWT token."""
    payload = {
        "sub": user_id,
        "email": email,
        "aud": "authenticated",
        "iat": datetime.utcnow().timestamp(),
        "exp": (datetime.utcnow() + timedelta(hours=1)).timestamp(),
        "user_metadata": {"role": role}
    }
    return jwt.encode(payload, os.environ['SUPABASE_JWT_SECRET'], algorithm="HS256")
    
    @patch('app.utils.export_control.logger')
    def test_blocked_export_is_audited(self, mock_logger, setup_env):
        """Test that blocked export attempts are properly audited."""
        # Import after env setup
        from app.utils.export_control import ExportController, ExportType
        
        os.environ['ALLOW_EXPORTS'] = 'false'
        
        controller = ExportController()
        allowed, reason = controller.is_export_allowed(
            ExportType.LEADS,
            "user@test.com",
            {"test": "parameter"}
        )
        
        assert not allowed
        assert "ALLOW_EXPORTS=false" in reason
        
        # Verify audit logging occurred
        mock_logger.warning.assert_called()
        call_args = mock_logger.warning.call_args[0][0]
        assert "AUDIT: Export attempt blocked" in call_args
        assert "user@test.com" in call_args
        assert "leads" in call_args
    
    @patch('app.utils.export_control.logger')
    def test_successful_export_is_audited(self, mock_logger, setup_env):
        """Test that successful exports are properly audited."""
        from app.utils.export_control import ExportController, ExportType
        
        os.environ['ALLOW_EXPORTS'] = 'true'
        
        controller = ExportController()
        
        # Create and process export request
        export_request = controller.create_export_request(
            export_type=ExportType.LEADS,
            requester="user@test.com",
            parameters={"format": "csv"}
        )
        
        result = controller.process_export_request(export_request)
        
        assert result.success
        assert result.allowed
        
        # Verify audit logging occurred
        mock_logger.info.assert_called()
        # Check that one of the calls contains audit information
        audit_logged = any("AUDIT: Export successful" in str(call) for call in mock_logger.info.call_args_list)
        assert audit_logged, "Expected audit log for successful export"


if __name__ == '__main__':
    pytest.main([__file__])