"""
Test for contractors table functionality and trial features.
"""

import sqlite3
import tempfile
from pathlib import Path
from datetime import datetime, timedelta
import sys
import os

# Add permit_leads to path to import our migration module
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from migrate_contractors import create_contractors_table


def test_contractors_table_creation():
    """Test that contractors table is created with correct schema."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp_db:
        db_path = Path(tmp_db.name)

    try:
        # Create the table
        create_contractors_table(db_path)

        # Verify table exists and has correct schema
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Check table exists
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='contractors'"
        )
        assert cursor.fetchone() is not None, "Contractors table should exist"

        # Check columns
        cursor.execute("PRAGMA table_info(contractors)")
        columns = {row[1]: row[2] for row in cursor.fetchall()}

        expected_columns = {
            "id": "INTEGER",
            "name": "TEXT",
            "email": "TEXT",
            "phone": "TEXT",
            "company": "TEXT",
            "password_hash": "TEXT",
            "trial_start_date": "TIMESTAMPTZ",
            "trial_end_date": "TIMESTAMPTZ",
            "subscription_status": "TEXT",
            "payment_method": "TEXT",
            "crypto_wallet_address": "TEXT",
            "created_at": "TEXT",
            "updated_at": "TEXT",
        }

        for col_name, col_type in expected_columns.items():
            assert col_name in columns, f"Column {col_name} should exist"
            assert (
                columns[col_name] == col_type
            ), f"Column {col_name} should be {col_type}"

        conn.close()
        print("✓ Contractors table creation test passed")

    finally:
        db_path.unlink()


def test_contractor_trial_workflow():
    """Test inserting contractor with trial data."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp_db:
        db_path = Path(tmp_db.name)

    try:
        # Create the table
        create_contractors_table(db_path)

        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Insert test contractor
        trial_start = datetime.now()
        trial_end = trial_start + timedelta(days=7)

        cursor.execute(
            """
            INSERT INTO contractors 
            (name, email, phone, company, password_hash, trial_start_date, trial_end_date, 
             subscription_status, payment_method, crypto_wallet_address)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                "John Doe",
                "john@example.com",
                "+1234567890",
                "Doe Construction",
                "hashed_password",
                trial_start.isoformat(),
                trial_end.isoformat(),
                "trial",
                "btc",
                "1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa",
            ),
        )

        conn.commit()

        # Verify data was inserted correctly
        cursor.execute(
            "SELECT * FROM contractors WHERE email = ?", ("john@example.com",)
        )
        contractor = cursor.fetchone()

        assert contractor is not None, "Contractor should be inserted"
        assert contractor[8] == "trial", "Subscription status should be trial"
        assert contractor[9] == "btc", "Payment method should be btc"
        assert (
            contractor[10] == "1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa"
        ), "Crypto address should be stored"

        # Test query for active trials
        cursor.execute(
            """
            SELECT * FROM contractors 
            WHERE subscription_status = 'trial' 
            AND trial_end_date > datetime('now')
        """
        )

        active_trials = cursor.fetchall()
        assert len(active_trials) == 1, "Should find one active trial"

        conn.close()
        print("✓ Contractor trial workflow test passed")

    finally:
        db_path.unlink()


def test_subscription_status_constraints():
    """Test that subscription_status constraints work."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp_db:
        db_path = Path(tmp_db.name)

    try:
        create_contractors_table(db_path)

        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Valid status should work
        cursor.execute(
            """
            INSERT INTO contractors (name, email, password_hash, subscription_status)
            VALUES (?, ?, ?, ?)
        """,
            ("Test User", "test@example.com", "hash", "active"),
        )

        # Invalid status should fail
        try:
            cursor.execute(
                """
                INSERT INTO contractors (name, email, password_hash, subscription_status)
                VALUES (?, ?, ?, ?)
            """,
                ("Test User 2", "test2@example.com", "hash", "invalid_status"),
            )
            conn.commit()
            assert False, "Should have failed with invalid subscription status"
        except sqlite3.IntegrityError:
            pass  # Expected

        conn.close()
        print("✓ Subscription status constraints test passed")

    finally:
        db_path.unlink()


if __name__ == "__main__":
    print("Running contractors table tests...")
    test_contractors_table_creation()
    test_contractor_trial_workflow()
    test_subscription_status_constraints()
    print("All tests passed! ✓")
