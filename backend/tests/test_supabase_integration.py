#!/usr/bin/env python3
"""
Test for the insert_lead function with Supabase integration.
"""

import pytest
import os
from unittest.mock import patch, MagicMock

# Set required environment variables for testing
os.environ["SUPABASE_JWT_SECRET"] = "test_secret"
os.environ["SUPABASE_URL"] = "https://test.supabase.co"
os.environ["SUPABASE_SERVICE_ROLE_KEY"] = "test_service_role"


def test_insert_lead_validation():
    """Test insert_lead function input validation."""
    from app.ingest import insert_lead

    # Test invalid input type
    with pytest.raises(ValueError, match="Lead must be a dictionary"):
        insert_lead("not a dict")

    # Test missing jurisdiction
    with pytest.raises(ValueError, match="jurisdiction is required"):
        insert_lead({})

    # Test missing permit_id
    with pytest.raises(ValueError, match="permit_id is required"):
        insert_lead({"jurisdiction": "test"})


@patch("app.ingest.get_supabase_client")
def test_insert_lead_success(mock_get_client):
    """Test successful lead insertion."""
    from app.ingest import insert_lead

    # Mock Supabase client and response
    mock_client = MagicMock()
    mock_table = MagicMock()
    mock_insert = MagicMock()
    mock_execute = MagicMock()

    # Set up the mock chain
    mock_get_client.return_value = mock_client
    mock_client.table.return_value = mock_table
    mock_table.insert.return_value = mock_insert
    mock_insert.execute.return_value.data = [
        {"id": 1, "jurisdiction": "test", "permit_id": "12345"}
    ]

    # Test data
    lead_data = {
        "jurisdiction": "test_jurisdiction",
        "permit_id": "12345",
        "address": "123 Test St",
        "value": 50000.0,
        "is_residential": True,
        "latitude": 29.7604,
        "longitude": -95.3698,
        "trade_tags": ["plumbing", "electrical"],
    }

    # Call the function
    result = insert_lead(lead_data)

    # Verify the result
    assert result["id"] == 1
    assert result["jurisdiction"] == "test"
    assert result["permit_id"] == "12345"

    # Verify Supabase was called correctly
    mock_client.table.assert_called_once_with("leads")
    mock_table.insert.assert_called_once()

    # Check that the data was cleaned properly
    insert_call_args = mock_table.insert.call_args[0][0]
    assert insert_call_args["jurisdiction"] == "test_jurisdiction"
    assert insert_call_args["permit_id"] == "12345"
    assert insert_call_args["address"] == "123 Test St"
    assert insert_call_args["value"] == 50000.0
    assert insert_call_args["is_residential"] is True
    assert insert_call_args["latitude"] == 29.7604
    assert insert_call_args["longitude"] == -95.3698
    assert insert_call_args["trade_tags"] == ["plumbing", "electrical"]


@patch("app.ingest.get_supabase_client")
def test_insert_lead_supabase_error(mock_get_client):
    """Test handling of Supabase errors."""
    from app.ingest import insert_lead

    # Mock Supabase client to raise an exception
    mock_client = MagicMock()
    mock_get_client.return_value = mock_client
    mock_client.table.side_effect = Exception("Supabase connection failed")

    lead_data = {"jurisdiction": "test_jurisdiction", "permit_id": "12345"}

    # Should raise an exception
    with pytest.raises(Exception, match="Failed to insert lead"):
        insert_lead(lead_data)


def test_supabase_client_env_validation():
    """Test Supabase client environment variable validation."""
    from app.supabase_client import get_supabase_client, reset_client

    # Reset client
    reset_client()

    # Save original values
    original_url = os.environ.get("SUPABASE_URL")
    original_key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")

    try:
        # Test missing URL
        del os.environ["SUPABASE_URL"]
        with pytest.raises(
            ValueError, match="SUPABASE_URL environment variable is required"
        ):
            get_supabase_client()

        # Restore URL, remove key
        os.environ["SUPABASE_URL"] = "https://test.supabase.co"
        del os.environ["SUPABASE_SERVICE_ROLE_KEY"]
        reset_client()

        with pytest.raises(
            ValueError,
            match="SUPABASE_SERVICE_ROLE_KEY environment variable is required",
        ):
            get_supabase_client()

    finally:
        # Restore original values
        if original_url:
            os.environ["SUPABASE_URL"] = original_url
        if original_key:
            os.environ["SUPABASE_SERVICE_ROLE_KEY"] = original_key
        reset_client()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
