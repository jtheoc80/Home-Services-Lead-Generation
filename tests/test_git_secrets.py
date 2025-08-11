#!/usr/bin/env python3
"""
Test suite for git-secrets configuration
This test demonstrates that git-secrets correctly prevents committing sensitive data
"""

import os
import subprocess
import tempfile
import unittest
from pathlib import Path


class GitSecretsTest(unittest.TestCase):
    """Test git-secrets functionality with various secret patterns"""

    def setUp(self):
        """Set up test environment"""
        self.repo_root = Path(__file__).parent.parent
        self.test_file = self.repo_root / "test_secrets_file.tmp"
        
    def tearDown(self):
        """Clean up test files"""
        if self.test_file.exists():
            self.test_file.unlink()
    
    def test_supabase_service_role_key_detection(self):
        """Test that Supabase service role keys are detected"""
        fake_key = "sb-1234567890abcdef1234567890abcdef12345678"
        
        # Write fake key to test file
        with open(self.test_file, 'w') as f:
            f.write(f"SUPABASE_SERVICE_ROLE_KEY={fake_key}\n")
        
        # Run git-secrets scan
        result = subprocess.run(
            ["git", "secrets", "--scan", str(self.test_file)],
            cwd=self.repo_root,
            capture_output=True,
            text=True
        )
        
        # Should fail (exit code 1) because secret was detected
        self.assertEqual(result.returncode, 1, 
                        "git-secrets should detect Supabase service role key")
        self.assertIn("sb-", result.stderr, 
                     "Error message should mention the detected pattern")
    
    def test_jwt_token_detection(self):
        """Test that JWT tokens are detected"""
        fake_jwt = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyfQ"
        
        # Write fake JWT to test file
        with open(self.test_file, 'w') as f:
            f.write(f"JWT_TOKEN={fake_jwt}\n")
        
        # Run git-secrets scan
        result = subprocess.run(
            ["git", "secrets", "--scan", str(self.test_file)],
            cwd=self.repo_root,
            capture_output=True,
            text=True
        )
        
        # Should fail because JWT was detected
        self.assertEqual(result.returncode, 1, 
                        "git-secrets should detect JWT tokens")
        self.assertIn("ey", result.stderr, 
                     "Error message should mention the detected pattern")
    
    def test_vercel_token_detection(self):
        """Test that Vercel tokens are detected"""
        fake_token = "vercel_1234567890abcdef1234567890"
        
        # Write fake token to test file
        with open(self.test_file, 'w') as f:
            f.write(f"VERCEL_TOKEN={fake_token}\n")
        
        # Run git-secrets scan
        result = subprocess.run(
            ["git", "secrets", "--scan", str(self.test_file)],
            cwd=self.repo_root,
            capture_output=True,
            text=True
        )
        
        # Should fail because Vercel token was detected
        self.assertEqual(result.returncode, 1, 
                        "git-secrets should detect Vercel tokens")
    
    def test_railway_token_detection(self):
        """Test that Railway tokens are detected"""
        fake_token = "railway_1234567890abcdef1234567890abcdef"
        
        # Write fake token to test file
        with open(self.test_file, 'w') as f:
            f.write(f"RAILWAY_TOKEN={fake_token}\n")
        
        # Run git-secrets scan
        result = subprocess.run(
            ["git", "secrets", "--scan", str(self.test_file)],
            cwd=self.repo_root,
            capture_output=True,
            text=True
        )
        
        # Should fail because Railway token was detected
        self.assertEqual(result.returncode, 1, 
                        "git-secrets should detect Railway tokens")
    
    def test_allowed_placeholder_values(self):
        """Test that placeholder values are allowed"""
        placeholders = [
            "your_supabase_jwt_secret_here",
            "your_mapbox_token_here",
            "sb-example-key-placeholder"
        ]
        
        # Write placeholder values to test file
        with open(self.test_file, 'w') as f:
            for placeholder in placeholders:
                f.write(f"KEY={placeholder}\n")
        
        # Run git-secrets scan
        result = subprocess.run(
            ["git", "secrets", "--scan", str(self.test_file)],
            cwd=self.repo_root,
            capture_output=True,
            text=True
        )
        
        # Should pass because these are allowed placeholder values
        self.assertEqual(result.returncode, 0, 
                        "git-secrets should allow placeholder values")
    
    def test_clean_file_passes(self):
        """Test that files without secrets pass the scan"""
        clean_content = """
# Configuration file
DEBUG=true
DATABASE_URL=postgresql://localhost/mydb
LOG_LEVEL=info
"""
        
        # Write clean content to test file
        with open(self.test_file, 'w') as f:
            f.write(clean_content)
        
        # Run git-secrets scan
        result = subprocess.run(
            ["git", "secrets", "--scan", str(self.test_file)],
            cwd=self.repo_root,
            capture_output=True,
            text=True
        )
        
        # Should pass because no secrets are present
        self.assertEqual(result.returncode, 0, 
                        "git-secrets should allow clean files")


def demonstrate_failing_test():
    """
    Sample failing test that demonstrates git-secrets blocking a commit
    This would fail in a real commit scenario
    """
    print("🧪 Demonstrating git-secrets detection...")
    print("This test creates a file with a fake Supabase key and shows how git-secrets blocks it.")
    
    # Create a temporary file with a fake secret
    repo_root = Path(__file__).parent.parent
    test_file = repo_root / "dangerous_secrets.tmp"
    
    try:
        # Write a fake Supabase service role key
        with open(test_file, 'w') as f:
            f.write("# This file contains a fake secret for testing\n")
            f.write("SUPABASE_SERVICE_ROLE_KEY=sb-1234567890abcdef1234567890abcdef12345678\n")
            f.write("# This would be blocked by git-secrets!\n")
        
        print(f"📝 Created test file: {test_file}")
        print("📄 File contents:")
        with open(test_file, 'r') as f:
            print(f.read())
        
        # Try to scan with git-secrets
        print("🔍 Running git-secrets scan...")
        result = subprocess.run(
            ["git", "secrets", "--scan", str(test_file)],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 1:
            print("🚫 BLOCKED! git-secrets detected a secret:")
            print(result.stderr)
            print("✅ Test successful - secret was blocked!")
        else:
            print("❌ Test failed - secret was not detected")
            
    finally:
        # Clean up
        if test_file.exists():
            test_file.unlink()
            print(f"🧹 Cleaned up test file: {test_file}")


if __name__ == "__main__":
    print("=" * 60)
    print("Git Secrets Test Suite")
    print("=" * 60)
    
    # Run the demonstration first
    demonstrate_failing_test()
    print("\n" + "=" * 60)
    print("Running unit tests...")
    print("=" * 60)
    
    # Run the unit tests
    unittest.main(verbosity=2)