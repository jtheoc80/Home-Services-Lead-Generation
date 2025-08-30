#!/usr/bin/env python3
"""
Environment Variables Validation Script

This script validates that all required environment variables are properly
configured for both Vercel (frontend) and Railway (backend) deployments.

Usage:
    python scripts/validate_env.py --mode=vercel
    python scripts/validate_env.py --mode=railway
    python scripts/validate_env.py --mode=ingestion
    python scripts/validate_env.py --mode=all
"""

import argparse
import os
import sys
from urllib.parse import urlparse


class EnvironmentValidator:
    """Validates environment variables for different deployment modes."""

    def __init__(self):
        self.errors = []
        self.warnings = []

    def validate_all(self) -> bool:
        """Validate all environment configurations."""
        vercel_ok = self.validate_vercel()
        railway_ok = self.validate_railway()
        ingestion_ok = self.validate_ingestion()
        return vercel_ok and railway_ok and ingestion_ok

    def validate_vercel(self) -> bool:
        """Validate Vercel environment variables."""
        print("🔍 Validating Vercel environment variables...")

        # Server-only secrets (must be set, not browser-accessible)
        server_secrets = ["STRIPE_WEBHOOK_SECRET", "SUPABASE_SERVICE_ROLE_KEY"]

        # Browser-safe variables (must start with NEXT_PUBLIC_)
        browser_safe = [
            "NEXT_PUBLIC_SUPABASE_URL",
            "NEXT_PUBLIC_SUPABASE_ANON_KEY",
            "NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY",
        ]

        # Optional but recommended
        optional = ["NEXT_PUBLIC_ENVIRONMENT", "NEXT_PUBLIC_API_BASE_URL"]

        # Validate server-only secrets
        for var in server_secrets:
            value = os.getenv(var)
            if not value:
                self.errors.append(f"Missing required server secret: {var}")
            elif var.startswith("NEXT_PUBLIC_"):
                self.errors.append(
                    f"Server secret {var} incorrectly prefixed with NEXT_PUBLIC_"
                )
            else:
                self._validate_specific_var(var, value)

        # Validate browser-safe variables
        for var in browser_safe:
            value = os.getenv(var)
            if not value:
                self.errors.append(f"Missing required browser-safe variable: {var}")
            elif not var.startswith("NEXT_PUBLIC_"):
                self.errors.append(
                    f"Browser-safe variable {var} must start with NEXT_PUBLIC_"
                )
            else:
                self._validate_specific_var(var, value)

        # Check optional variables
        for var in optional:
            value = os.getenv(var)
            if not value:
                self.warnings.append(f"Optional variable not set: {var}")

        return len(self.errors) == 0

    def validate_railway(self) -> bool:
        """Validate Railway environment variables."""
        print("🚂 Validating Railway environment variables...")

        # Required for Railway backend
        required = [
            "DATABASE_URL",
            "STRIPE_SECRET_KEY",
            "STRIPE_PUBLISHABLE_KEY",
            "SUPABASE_SERVICE_ROLE_KEY",
            "SUPABASE_URL",
        ]

        # Optional but recommended
        optional = [
            "REDIS_URL",
            "SENDGRID_API_KEY",
            "TWILIO_ACCOUNT_SID",
            "TWILIO_AUTH_TOKEN",
        ]

        for var in required:
            value = os.getenv(var)
            if not value:
                self.errors.append(f"Missing required Railway variable: {var}")
            else:
                self._validate_specific_var(var, value)

        for var in optional:
            value = os.getenv(var)
            if not value:
                self.warnings.append(f"Optional Railway variable not set: {var}")

        return len(self.errors) == 0

    def validate_ingestion(self) -> bool:
        """Validate environment variables for data ingestion."""
        print("📊 Validating ingestion environment variables...")

        required = ["DATABASE_URL", "SUPABASE_SERVICE_ROLE_KEY"]

        optional = ["REDIS_URL", "DRY_RUN"]

        for var in required:
            value = os.getenv(var)
            if not value:
                self.errors.append(f"Missing required ingestion variable: {var}")
            else:
                self._validate_specific_var(var, value)

        for var in optional:
            value = os.getenv(var)
            if not value:
                self.warnings.append(f"Optional ingestion variable not set: {var}")

        return len(self.errors) == 0

    def _validate_specific_var(self, var_name: str, value: str) -> None:
        """Validate specific environment variable formats."""

        if var_name == "DATABASE_URL":
            if not value.startswith(("postgresql://", "postgres://")):
                self.errors.append(
                    f"{var_name} must start with postgresql:// or postgres://"
                )
            else:
                parsed = urlparse(value)
                if not parsed.hostname:
                    self.errors.append(f"{var_name} missing hostname")
                if not parsed.username:
                    self.errors.append(f"{var_name} missing username")
                if not parsed.password:
                    self.warnings.append(
                        f"{var_name} missing password (might be required)"
                    )

        elif var_name in ["NEXT_PUBLIC_SUPABASE_URL", "SUPABASE_URL"]:
            if not value.startswith("https://"):
                self.errors.append(f"{var_name} must start with https://")
            if not value.endswith(".supabase.co"):
                self.warnings.append(f"{var_name} doesn't look like a Supabase URL")

        elif var_name in ["SUPABASE_SERVICE_ROLE_KEY", "NEXT_PUBLIC_SUPABASE_ANON_KEY"]:
            if len(value) < 100:
                self.warnings.append(f"{var_name} seems too short for a Supabase key")
            if not value.startswith("eyJ"):
                self.warnings.append(f"{var_name} doesn't look like a JWT token")

        elif var_name == "STRIPE_WEBHOOK_SECRET":
            if not value.startswith("whsec_"):
                self.errors.append(f"{var_name} must start with whsec_")

        elif var_name == "STRIPE_SECRET_KEY":
            if not value.startswith(("sk_test_", "sk_live_")):
                self.errors.append(f"{var_name} must start with sk_test_ or sk_live_")

        elif var_name in [
            "STRIPE_PUBLISHABLE_KEY",
            "NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY",
        ]:
            if not value.startswith(("pk_test_", "pk_live_")):
                self.errors.append(f"{var_name} must start with pk_test_ or pk_live_")

        elif var_name == "REDIS_URL":
            if not value.startswith(("redis://", "rediss://")):
                self.errors.append(f"{var_name} must start with redis:// or rediss://")

        elif var_name == "SENDGRID_API_KEY":
            if not value.startswith("SG."):
                self.warnings.append(f"{var_name} doesn't look like a SendGrid API key")

        elif var_name == "TWILIO_ACCOUNT_SID":
            if not value.startswith("AC"):
                self.warnings.append(
                    f"{var_name} doesn't look like a Twilio Account SID"
                )

    def print_results(self) -> None:
        """Print validation results."""
        if self.errors:
            print("\n❌ ERRORS:")
            for error in self.errors:
                print(f"  • {error}")

        if self.warnings:
            print("\n⚠️  WARNINGS:")
            for warning in self.warnings:
                print(f"  • {warning}")

        if not self.errors and not self.warnings:
            print("\n✅ All environment variables are properly configured!")
        elif not self.errors:
            print(f"\n✅ No critical errors found ({len(self.warnings)} warnings)")
        else:
            print(
                f"\n❌ Found {len(self.errors)} errors and {len(self.warnings)} warnings"
            )

    def has_errors(self) -> bool:
        """Check if validation found any errors."""
        return len(self.errors) > 0


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(description="Validate environment variables")
    parser.add_argument(
        "--mode",
        choices=["vercel", "railway", "ingestion", "all"],
        default="all",
        help="Validation mode",
    )
    parser.add_argument("--env-file", type=str, help="Load environment from file")

    args = parser.parse_args()

    # Load environment file if specified
    if args.env_file:
        try:
            from dotenv import load_dotenv

            load_dotenv(args.env_file)
            print(f"📁 Loaded environment from {args.env_file}")
        except ImportError:
            print("⚠️  python-dotenv not installed, skipping env file loading")
        except Exception as e:
            print(f"❌ Failed to load env file: {e}")
            sys.exit(1)

    # Initialize validator
    validator = EnvironmentValidator()

    # Run validation based on mode
    try:
        if args.mode == "vercel":
            success = validator.validate_vercel()
        elif args.mode == "railway":
            validator.validate_railway()
        elif args.mode == "ingestion":
            success = validator.validate_ingestion()
        elif args.mode == "all":
            success = validator.validate_all()
        else:
            print(f"❌ Unknown mode: {args.mode}")
            sys.exit(1)

        # Print results
        validator.print_results()

        # Exit with appropriate code
        if validator.has_errors():
            print(
                "\n💡 Tip: Check the README 'Required Secrets' section for setup instructions"
            )
            sys.exit(1)
        else:
            print("\n🎉 Environment validation passed!")
            sys.exit(0)

    except Exception as e:
        print(f"❌ Validation failed with error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
