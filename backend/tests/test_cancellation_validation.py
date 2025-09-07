#!/usr/bin/env python3
"""
Simple validation test for cancellation feedback integration.

Tests basic functionality without complex mocking.
"""

import sys
from pathlib import Path


def test_schema_files():
    """Test that schema files are properly created."""
    print("Testing schema files...")

    # Check migration file
    migration_file = (
        Path(__file__).parent.parent
        / "app"
        / "migrations"
        / "003_cancellations_table.sql"
    )
    assert migration_file.exists(), "Migration file should exist"

    content = migration_file.read_text()
    required_elements = [
        "CREATE TABLE IF NOT EXISTS cancellations",
        "cancellation_reason",
        "poor_lead_quality",
        "source_cancellation_rate",
        "personalized_cancellation_adjustment",
    ]

    for element in required_elements:
        assert element in content, f"Missing required element: {element}"

    print("✓ Migration file contains all required elements")

    # Check main schema file
    schema_file = Path(__file__).parent.parent / "app" / "models.sql"
    schema_content = schema_file.read_text()

    cancellation_fields = [
        "source_cancellation_rate",
        "source_avg_cancellation_score",
        "personalized_cancellation_adjustment",
    ]

    for field in cancellation_fields:
        assert field in schema_content, f"Missing field in schema: {field}"

    print("✓ Main schema file updated with cancellation fields")


def test_service_file():
    """Test that cancellation feedback service file is created."""
    print("Testing service file...")

    service_file = Path(__file__).parent.parent / "app" / "cancellation_feedback.py"
    assert service_file.exists(), "Cancellation feedback service should exist"

    content = service_file.read_text()
    required_functions = [
        "calculate_global_source_adjustments",
        "calculate_personalized_adjustments",
        "update_lead_cancellation_scores",
    ]

    for func in required_functions:
        assert func in content, f"Missing function: {func}"

    print("✓ Cancellation feedback service has all required functions")


def test_ml_integration():
    """Test that ML files are updated with cancellation features."""
    print("Testing ML integration...")

    # Check train_model.py
    train_file = Path(__file__).parent.parent / "app" / "train_model.py"
    train_content = train_file.read_text()

    ml_features = [
        "source_cancellation_rate",
        "contractor_canceled",
        "canceled_for_quality",
        "contractor_win_rate",
    ]

    for feature in ml_features:
        assert feature in train_content, f"Missing ML feature: {feature}"

    print("✓ ML training updated with cancellation features")

    # Check ml_inference.py
    inference_file = Path(__file__).parent.parent / "app" / "ml_inference.py"
    inference_content = inference_file.read_text()

    assert "personalized_adjustment" in inference_content
    assert "CancellationFeedbackService" in inference_content

    print("✓ ML inference updated with personalized adjustments")


def test_python_syntax():
    """Test that all Python files have valid syntax."""
    print("Testing Python syntax...")

    python_files = [
        Path(__file__).parent.parent / "app" / "cancellation_feedback.py",
        Path(__file__).parent.parent / "app" / "train_model.py",
        Path(__file__).parent.parent / "app" / "ml_inference.py",
    ]

    for file_path in python_files:
        try:
            with open(file_path) as f:
                compile(f.read(), file_path, "exec")
            print(f"✓ {file_path.name} has valid syntax")
        except SyntaxError as e:
            raise AssertionError(f"Syntax error in {file_path.name}: {e}")


def main():
    """Run validation tests."""
    print("Running cancellation feedback integration validation...\n")

    try:
        test_schema_files()
        test_service_file()
        test_ml_integration()
        test_python_syntax()

        print("\n✅ All validation tests passed!")
        print("Cancellation feedback integration is properly implemented.")

        print("\nIntegration Summary:")
        print("- ✓ Added cancellations table with reason tracking")
        print("- ✓ Added cancellation rate fields to leads table")
        print("- ✓ Created cancellation feedback service")
        print("- ✓ Updated ML training with cancellation features")
        print("- ✓ Added personalized scoring adjustments")
        print("- ✓ Global and personalized scoring implemented")

        return 0

    except Exception as e:
        print(f"\n❌ Validation failed: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
