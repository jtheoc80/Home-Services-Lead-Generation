#!/usr/bin/env python3
"""
Tests for the Supabase authentication module.

This module tests JWT token verification and authentication functionality.
"""

import os
import jwt
import unittest
import sys
from datetime import datetime, timedelta

# Add the backend app directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "app"))

from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials


class TestSupabaseAuth(unittest.TestCase):
    """Test Supabase authentication functionality."""

    def setUp(self):
        """Set up test environment."""
        # Ensure we have a test JWT secret
        self.test_jwt_secret = "test_supabase_jwt_secret_for_testing_only"
        os.environ["SUPABASE_JWT_SECRET"] = self.test_jwt_secret

        # Import auth module after setting environment variable
        from auth import verify_jwt_token, auth_user, AuthUser

        self.verify_jwt_token = verify_jwt_token
        self.auth_user = auth_user
        self.AuthUser = AuthUser

    def tearDown(self):
        """Clean up test environment."""
        if "SUPABASE_JWT_SECRET" in os.environ:
            del os.environ["SUPABASE_JWT_SECRET"]

    def create_test_token(self, payload, secret=None, algorithm="HS256"):
        """Create a test JWT token."""
        if secret is None:
            secret = self.test_jwt_secret
        return jwt.encode(payload, secret, algorithm=algorithm)

    def test_verify_valid_jwt_token(self):
        """Test verification of a valid JWT token."""
        # Create a valid token payload
        payload = {
            "sub": "user123",
            "email": "test@example.com",
            "aud": "authenticated",
            "iat": datetime.utcnow().timestamp(),
            "exp": (datetime.utcnow() + timedelta(hours=1)).timestamp(),
        }

        token = self.create_test_token(payload)

        # Verify the token
        decoded_payload = self.verify_jwt_token(token)

        self.assertEqual(decoded_payload["sub"], "user123")
        self.assertEqual(decoded_payload["email"], "test@example.com")
        self.assertEqual(decoded_payload["aud"], "authenticated")

    def test_verify_expired_jwt_token(self):
        """Test verification of an expired JWT token."""
        # Create an expired token payload
        payload = {
            "sub": "user123",
            "email": "test@example.com",
            "aud": "authenticated",
            "iat": (datetime.utcnow() - timedelta(hours=2)).timestamp(),
            "exp": (datetime.utcnow() - timedelta(hours=1)).timestamp(),
        }

        token = self.create_test_token(payload)

        # Verify the token raises HTTPException for expired token
        with self.assertRaises(HTTPException) as context:
            self.verify_jwt_token(token)

        self.assertEqual(context.exception.status_code, 401)
        self.assertIn("expired", context.exception.detail.lower())

    def test_verify_invalid_jwt_token(self):
        """Test verification of an invalid JWT token."""
        # Create a token with wrong secret
        payload = {
            "sub": "user123",
            "email": "test@example.com",
            "aud": "authenticated",
            "iat": datetime.utcnow().timestamp(),
            "exp": (datetime.utcnow() + timedelta(hours=1)).timestamp(),
        }

        token = self.create_test_token(payload, secret="wrong_secret")

        # Verify the token raises HTTPException for invalid token
        with self.assertRaises(HTTPException) as context:
            self.verify_jwt_token(token)

        self.assertEqual(context.exception.status_code, 401)
        self.assertIn("invalid", context.exception.detail.lower())

    def test_verify_malformed_jwt_token(self):
        """Test verification of a malformed JWT token."""
        malformed_token = "not.a.valid.jwt.token"

        # Verify the token raises HTTPException for malformed token
        with self.assertRaises(HTTPException) as context:
            self.verify_jwt_token(malformed_token)

        self.assertEqual(context.exception.status_code, 401)
        self.assertIn("invalid", context.exception.detail.lower())

    def test_auth_user_valid_token(self):
        """Test auth_user dependency with valid token."""
        # Create a valid token
        payload = {
            "sub": "user123",
            "email": "test@example.com",
            "aud": "authenticated",
            "iat": datetime.utcnow().timestamp(),
            "exp": (datetime.utcnow() + timedelta(hours=1)).timestamp(),
        }

        token = self.create_test_token(payload)

        # Create mock credentials
        credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)

        # Test auth_user dependency
        user = self.auth_user(credentials)

        self.assertIsInstance(user, self.AuthUser)
        self.assertEqual(user.account_id, "user123")
        self.assertEqual(user.email, "test@example.com")
        self.assertEqual(user.payload["sub"], "user123")

    def test_auth_user_missing_user_id(self):
        """Test auth_user dependency with token missing user ID."""
        # Create a token without 'sub' field
        payload = {
            "email": "test@example.com",
            "aud": "authenticated",
            "iat": datetime.utcnow().timestamp(),
            "exp": (datetime.utcnow() + timedelta(hours=1)).timestamp(),
        }

        token = self.create_test_token(payload)

        credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)

        # Should raise HTTPException for missing user ID
        with self.assertRaises(HTTPException) as context:
            self.auth_user(credentials)

        self.assertEqual(context.exception.status_code, 401)
        self.assertIn("missing user id", context.exception.detail.lower())

    def test_auth_user_missing_email(self):
        """Test auth_user dependency with token missing email."""
        # Create a token without 'email' field
        payload = {
            "sub": "user123",
            "aud": "authenticated",
            "iat": datetime.utcnow().timestamp(),
            "exp": (datetime.utcnow() + timedelta(hours=1)).timestamp(),
        }

        token = self.create_test_token(payload)

        credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)

        # Should raise HTTPException for missing email
        with self.assertRaises(HTTPException) as context:
            self.auth_user(credentials)

        self.assertEqual(context.exception.status_code, 401)
        self.assertIn("missing email", context.exception.detail.lower())

    def test_auth_user_class(self):
        """Test AuthUser class functionality."""
        payload = {"sub": "user123", "email": "test@example.com", "role": "user"}

        user = self.AuthUser(
            account_id="user123", email="test@example.com", payload=payload
        )

        self.assertEqual(user.account_id, "user123")
        self.assertEqual(user.email, "test@example.com")
        self.assertEqual(user.payload["role"], "user")


class TestEnvironmentValidation(unittest.TestCase):
    """Test environment variable validation for auth."""

    def test_missing_jwt_secret_raises_error(self):
        """Test that missing SUPABASE_JWT_SECRET raises ValueError."""
        # Remove JWT secret if it exists
        if "SUPABASE_JWT_SECRET" in os.environ:
            del os.environ["SUPABASE_JWT_SECRET"]

        # Clear auth module from sys.modules to force re-import
        if "auth" in sys.modules:
            del sys.modules["auth"]

        # Importing auth module should raise ValueError
        with self.assertRaises(ValueError) as context:
            pass

        self.assertIn("SUPABASE_JWT_SECRET", str(context.exception))

    def setUp(self):
        """Clean up modules before each test."""
        # Remove auth module from cache to ensure fresh import
        if "auth" in sys.modules:
            del sys.modules["auth"]

    def tearDown(self):
        """Clean up after each test."""
        # Restore environment for other tests
        os.environ["SUPABASE_JWT_SECRET"] = "test_secret"


if __name__ == "__main__":
    unittest.main()
