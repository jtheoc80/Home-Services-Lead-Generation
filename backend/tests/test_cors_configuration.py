"""
Test CORS middleware configuration for the FastAPI application.
"""

import os
import sys
import pytest

# Set required environment variables before any imports
os.environ["SUPABASE_JWT_SECRET"] = "test_secret"
os.environ["SUPABASE_URL"] = "https://test.supabase.co"
os.environ["SUPABASE_SERVICE_ROLE_KEY"] = "test_role"

# Add the app directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

# Import the app after setting environment variables
from main import app


class TestCORSConfiguration:
    """Test CORS middleware configuration."""

    def test_cors_middleware_configured(self):
        """Test that CORS middleware is properly configured."""
        # Check that CORS middleware is in the middleware stack
        cors_middleware_found = False
        for middleware in app.user_middleware:
            if hasattr(middleware, "cls") and "CORS" in str(middleware.cls):
                cors_middleware_found = True
                break

        assert cors_middleware_found, "CORS middleware should be configured"

    def test_cors_origins_configuration(self):
        """Test that CORS origins are configured correctly."""
        # Get the CORS middleware instance
        cors_middleware = None
        for middleware in app.user_middleware:
            if hasattr(middleware, "cls") and "CORS" in str(middleware.cls):
                cors_middleware = middleware
                break

        assert cors_middleware is not None, "CORS middleware should be found"

        # The middleware kwargs should contain our expected origins
        expected_origins = [
            "http://localhost:3000",
            "https://<your-staging-domain>",
            "https://<your-prod-domain>",
        ]

        # Check the middleware was configured with the expected parameters
        if hasattr(cors_middleware, "kwargs"):
            origins = cors_middleware.kwargs.get("allow_origins", [])
            for expected_origin in expected_origins:
                assert (
                    expected_origin in origins
                ), f"Expected origin {expected_origin} should be in CORS configuration"
        else:
            # If kwargs not available, we can still verify by checking the source
            # This is a fallback validation
            pytest.skip("Cannot access middleware kwargs directly")

    def test_cors_other_settings(self):
        """Test that other CORS settings are configured correctly."""
        # Get the CORS middleware instance
        cors_middleware = None
        for middleware in app.user_middleware:
            if hasattr(middleware, "cls") and "CORS" in str(middleware.cls):
                cors_middleware = middleware
                break

        assert cors_middleware is not None, "CORS middleware should be found"

        # Check other CORS settings
        if hasattr(cors_middleware, "kwargs"):
            kwargs = cors_middleware.kwargs
            assert (
                kwargs.get("allow_credentials") is True
            ), "CORS should allow credentials"
            assert kwargs.get("allow_methods") == ["*"], "CORS should allow all methods"
            assert kwargs.get("allow_headers") == ["*"], "CORS should allow all headers"
        else:
            pytest.skip("Cannot access middleware kwargs directly")


def test_cors_configuration_in_source():
    """Test that the CORS configuration matches the expected format by checking source."""
    # Read the main.py file to verify the configuration
    import inspect

    # Get the source file of the main module
    main_file = inspect.getfile(sys.modules["main"])

    with open(main_file, "r") as f:
        content = f.read()

    # Check that the expected origins are in the source
    assert (
        "http://localhost:3000" in content
    ), "localhost:3000 should be in CORS origins"
    assert (
        "https://<your-staging-domain>" in content
    ), "staging domain placeholder should be in CORS origins"
    assert (
        "https://<your-prod-domain>" in content
    ), "prod domain placeholder should be in CORS origins"

    # Check that the old 127.0.0.1 origin is not present anymore
    assert (
        "http://127.0.0.1:3000" not in content
    ), "127.0.0.1:3000 should not be in CORS origins"

    # Check other CORS settings are present
    assert "allow_credentials=True" in content, "CORS should allow credentials"
    assert 'allow_methods=["*"]' in content, "CORS should allow all methods"
    assert 'allow_headers=["*"]' in content, "CORS should allow all headers"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
