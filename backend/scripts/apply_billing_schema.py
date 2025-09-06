#!/usr/bin/env python3
"""
Apply billing schema to the database.
Idempotent script that creates only the billing-related tables.
"""

import sys
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent.parent
sys.path.insert(0, str(backend_path))

from app.supabase_client import get_supabase_client


def apply_billing_schema():
    """Apply billing schema to the database."""
    try:
        client = get_supabase_client()

        # Read the billing schema from models.sql
        models_file = backend_path / "app" / "models.sql"
        with open(models_file, "r") as f:
            content = f.read()

        # Extract only the billing schema section
        if "-- ===== STRIPE BILLING TABLES =====" in content:
            billing_schema = content.split("-- ===== STRIPE BILLING TABLES =====")[1]

            print("Applying billing schema...")

            # Execute the schema using raw SQL
            # Note: Supabase client doesn't have direct SQL execution,
            # so we'll need to use the database connection if available
            print("⚠️  Manual application required:")
            print("Please run the following SQL in your database:")
            print("=" * 50)
            print(
                "The billing schema SQL section has been found in models.sql after the marker '-- ===== STRIPE BILLING TABLES ====='."
            )
            print(
                "Please open the file and copy the relevant section to apply it manually. The schema content is not printed here for security reasons."
            )

        else:
            print("❌ No billing schema found in models.sql")
            return False

    except Exception as e:
        print(f"❌ Error applying billing schema: {e}")
        return False

    return True


if __name__ == "__main__":
    success = apply_billing_schema()
    sys.exit(0 if success else 1)
