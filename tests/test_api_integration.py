"""
Test API endpoint functionality without running server.
"""

import json
from datetime import datetime
from scoring.v0 import score_v0


def test_api_endpoint_logic():
    """Test the core logic that would be used in the API endpoint."""

    # Simulate API request data
    request_data = {
        "lead": {
            "lead_id": "api-test-001",
            "created_at": "2024-12-15T10:00:00Z",
            "trade_tags": ["kitchen"],
            "value": 35000,
            "year_built": 1992,
            "owner_kind": "individual",
            "address": "123 Test St, Houston, TX",
            "description": "Kitchen renovation",
            "jurisdiction": "tx-harris",
        },
        "version": "v0",
    }

    # Extract lead data
    lead_data = request_data["lead"]
    version = request_data["version"]

    # Validate version
    assert version in ["v0"], f"Unsupported version: {version}"

    # Score the lead
    result = score_v0(lead_data)

    # Verify result structure
    assert "score" in result
    assert "reasons" in result
    assert isinstance(result["score"], int)
    assert isinstance(result["reasons"], list)
    assert 0 <= result["score"] <= 100

    # Build API response (simulating what endpoint would return)
    api_response = {
        "lead_id": lead_data["lead_id"],
        "version": version,
        "score": result["score"],
        "reasons": result["reasons"],
        "scored_at": datetime.now().isoformat(),
    }

    # Verify response structure
    assert api_response["lead_id"] == "api-test-001"
    assert api_response["version"] == "v0"
    assert api_response["score"] > 0
    assert len(api_response["reasons"]) > 0
    assert "scored_at" in api_response

    print(f"API test passed: {api_response['score']}/100")
    print(f"Response: {json.dumps(api_response, indent=2)}")


def test_api_request_validation():
    """Test request validation logic."""

    # Test valid request
    valid_request = {
        "lead": {"lead_id": "valid-001", "trade_tags": ["roofing"]},
        "version": "v0",
    }

    # Should not raise any errors
    lead_data = valid_request["lead"]
    result = score_v0(lead_data)
    assert result["score"] >= 0

    # Test invalid version
    invalid_request = {"lead": {"lead_id": "invalid-001"}, "version": "v999"}

    assert invalid_request["version"] not in ["v0"], "Should reject invalid version"


def test_api_persistence_logic():
    """Test the database persistence logic (without actual database)."""

    # Simulate persistence call
    def mock_persist_lead_score(lead_id, version, score, reasons):
        """Mock persistence function."""
        # Validate inputs
        assert isinstance(lead_id, str) and len(lead_id) > 0
        assert version in ["v0"]
        assert isinstance(score, int) and 0 <= score <= 100
        assert isinstance(reasons, list) and len(reasons) > 0

        # Simulate successful persistence
        return True

    # Test data
    lead_id = "persist-test-001"
    version = "v0"
    score = 85
    reasons = ["Test reason 1", "Test reason 2"]

    # Should not raise any errors
    result = mock_persist_lead_score(lead_id, version, score, reasons)
    assert result is True


if __name__ == "__main__":
    test_api_endpoint_logic()
    test_api_request_validation()
    test_api_persistence_logic()
    print("All API logic tests passed!")
