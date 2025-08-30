#!/usr/bin/env python3
"""
Demo script showing the ALLOW_EXPORTS=false enforcement with admin override.

This script demonstrates:
1. ALLOW_EXPORTS=false is enforced server-side
2. Non-admin users get 403 when attempting exports
3. Admin users can override using admin_override=true
4. All attempts are audited with structured logging
"""

import requests
import jwt
from datetime import datetime, timedelta

# Configuration
API_BASE = "http://localhost:8000"
JWT_SECRET = "test_secret"


def create_jwt_token(user_id: str, email: str, role: str = "user") -> str:
    """Create a test JWT token."""
    payload = {
        "sub": user_id,
        "email": email,
        "aud": "authenticated",
        "iat": datetime.utcnow().timestamp(),
        "exp": (datetime.utcnow() + timedelta(hours=1)).timestamp(),
        "user_metadata": {"role": role},
    }
    return jwt.encode(payload, JWT_SECRET, algorithm="HS256")


def demo_export_security():
    """Demonstrate export security enforcement."""

    print("🔒 Export Security Demo - ALLOW_EXPORTS=false Enforcement")
    print("=" * 60)

    # Create test tokens
    user_token = create_jwt_token("user123", "user@test.com", "user")
    admin_token = create_jwt_token("admin123", "admin@test.com", "admin")

    headers_user = {
        "Authorization": f"Bearer {user_token}",
        "Content-Type": "application/json",
    }
    headers_admin = {
        "Authorization": f"Bearer {admin_token}",
        "Content-Type": "application/json",
    }

    export_request = {"export_type": "leads", "format": "csv"}

    print("\n1. ❌ Non-admin user attempting export (should get 403)")
    response = requests.post(
        f"{API_BASE}/api/export/data", json=export_request, headers=headers_user
    )
    print(f"   Status: {response.status_code}")
    print(f"   Response: {response.json()}")

    print("\n2. ❌ Non-admin user attempting admin override (should get 403)")
    override_request = {**export_request, "admin_override": True}
    response = requests.post(
        f"{API_BASE}/api/export/data", json=override_request, headers=headers_user
    )
    print(f"   Status: {response.status_code}")
    print(f"   Response: {response.json()}")

    print("\n3. ❌ Admin user without override (should get 403)")
    response = requests.post(
        f"{API_BASE}/api/export/data", json=export_request, headers=headers_admin
    )
    print(f"   Status: {response.status_code}")
    print(f"   Response: {response.json()}")

    print("\n4. ✅ Admin user with override (should get 200)")
    response = requests.post(
        f"{API_BASE}/api/export/data", json=override_request, headers=headers_admin
    )
    print(f"   Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"   Export ID: {data['export_id']}")
        print(f"   Allowed via: {data['allowed_via']}")
        print(f"   Timestamp: {data['timestamp']}")
    else:
        print(f"   Response: {response.json()}")

    print("\n5. 📊 Export status for admin user")
    response = requests.get(f"{API_BASE}/api/export/status", headers=headers_admin)
    if response.status_code == 200:
        data = response.json()
        print(f"   Exports enabled: {data['exports_enabled']}")
        print(f"   User is admin: {data['user_is_admin']}")
        print(f"   Admin override available: {data['admin_override_available']}")
        print(f"   Message: {data['message']}")

    print("\n6. 📊 Export status for regular user")
    response = requests.get(f"{API_BASE}/api/export/status", headers=headers_user)
    if response.status_code == 200:
        data = response.json()
        print(f"   Exports enabled: {data['exports_enabled']}")
        print(f"   User is admin: {data['user_is_admin']}")
        print(f"   Admin override available: {data['admin_override_available']}")
        print(f"   Message: {data['message']}")

    print("\n✅ Demo complete! Check server logs for audit entries.")


if __name__ == "__main__":
    try:
        demo_export_security()
    except requests.ConnectionError:
        print("❌ Error: Could not connect to server at http://localhost:8000")
        print("Please start the server first with:")
        print(
            "ALLOW_EXPORTS=false SUPABASE_JWT_SECRET=test_secret uvicorn main:app --port 8000"
        )
