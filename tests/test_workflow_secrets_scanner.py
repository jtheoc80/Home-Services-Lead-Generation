#!/usr/bin/env python3
"""
Test suite for the workflow secrets scanner

This tests that the scanner correctly finds secret patterns and determines
whether they are required or optional.
"""

import unittest
import tempfile
import os
from pathlib import Path
import sys

# Add the scripts directory to the path so we can import the scanner
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts'))

from scan_workflow_secrets import WorkflowSecretsScanner, SecretUsage


class TestWorkflowSecretsScanner(unittest.TestCase):
    """Test the workflow secrets scanner functionality"""

    def setUp(self):
        """Set up test environment with temporary directory"""
        self.temp_dir = tempfile.mkdtemp()
        self.workflows_dir = Path(self.temp_dir) / "workflows"
        self.workflows_dir.mkdir()

    def tearDown(self):
        """Clean up temporary files"""
        import shutil
        shutil.rmtree(self.temp_dir)

    def create_test_workflow(self, filename: str, content: str):
        """Helper to create a test workflow file"""
        workflow_file = self.workflows_dir / filename
        with open(workflow_file, 'w') as f:
            f.write(content)
        return workflow_file

    def test_supabase_secret_detection(self):
        """Test that Supabase secrets are detected correctly"""
        content = """
name: Test Workflow
on: workflow_dispatch
jobs:
  test:
    runs-on: ubuntu-latest
    env:
      SUPABASE_URL: ${{ secrets.SUPABASE_URL }}
      SUPABASE_SERVICE_ROLE_KEY: ${{ secrets.SUPABASE_SERVICE_ROLE_KEY }}
    steps:
      - name: Test step
        run: echo "test"
"""
        self.create_test_workflow("test.yml", content)
        
        scanner = WorkflowSecretsScanner(str(self.workflows_dir))
        usages = scanner.scan_all_workflows()
        
        # Should find both Supabase secrets
        secret_names = {usage.secret_name for usage in usages}
        self.assertIn("SUPABASE_URL", secret_names)
        self.assertIn("SUPABASE_SERVICE_ROLE_KEY", secret_names)
        
        # Both should be marked as required
        for usage in usages:
            self.assertTrue(usage.is_required)

    def test_permits_url_detection(self):
        """Test that permit URL secrets are detected"""
        content = """
name: Permits Workflow
on: workflow_dispatch
jobs:
  scrape:
    runs-on: ubuntu-latest
    env:
      HC_PERMITS_URL: ${{ secrets.HC_ISSUED_PERMITS_URL }}
      DALLAS_URL: ${{ secrets.DALLAS_PERMITS_URL }}
    steps:
      - name: Scrape
        run: echo "scraping"
"""
        self.create_test_workflow("permits.yml", content)
        
        scanner = WorkflowSecretsScanner(str(self.workflows_dir))
        usages = scanner.scan_all_workflows()
        
        secret_names = {usage.secret_name for usage in usages}
        self.assertIn("HC_ISSUED_PERMITS_URL", secret_names)
        self.assertIn("DALLAS_PERMITS_URL", secret_names)

    def test_vercel_railway_token_detection(self):
        """Test that Vercel and Railway tokens are detected"""
        content = """
name: Deploy Workflow
on: workflow_dispatch
jobs:
  deploy:
    runs-on: ubuntu-latest
    env:
      VERCEL_TOKEN: ${{ secrets.VERCEL_TOKEN }}
      RAILWAY_TOKEN: ${{ secrets.RAILWAY_TOKEN }}
    steps:
      - name: Deploy
        run: echo "deploying"
"""
        self.create_test_workflow("deploy.yml", content)
        
        scanner = WorkflowSecretsScanner(str(self.workflows_dir))
        usages = scanner.scan_all_workflows()
        
        secret_names = {usage.secret_name for usage in usages}
        self.assertIn("VERCEL_TOKEN", secret_names)
        self.assertIn("RAILWAY_TOKEN", secret_names)

    def test_optional_secret_with_fallback(self):
        """Test that secrets with fallbacks are detected as optional"""
        content = """
name: Test Fallback
on: workflow_dispatch
jobs:
  test:
    runs-on: ubuntu-latest
    env:
      SOURCE_URL: ${{ secrets.HC_ISSUED_PERMITS_URL || 'default-url' }}
    steps:
      - name: Test
        run: echo "test"
"""
        self.create_test_workflow("fallback.yml", content)
        
        scanner = WorkflowSecretsScanner(str(self.workflows_dir))
        usages = scanner.scan_all_workflows()
        
        # Should find the secret
        self.assertEqual(len(usages), 1)
        usage = usages[0]
        self.assertEqual(usage.secret_name, "HC_ISSUED_PERMITS_URL")
        # Should be marked as optional due to fallback to default
        self.assertFalse(usage.is_required)

    def test_required_secret_with_validation(self):
        """Test that secrets with validation checks are marked as required"""
        content = """
name: Test Validation
on: workflow_dispatch
jobs:
  test:
    runs-on: ubuntu-latest
    env:
      VERCEL_TOKEN: ${{ secrets.VERCEL_TOKEN }}
    steps:
      - name: Validate
        run: |
          if [ -z "${{ env.VERCEL_TOKEN }}" ]; then
            echo "Error: VERCEL_TOKEN secret is not set"
            exit 1
          fi
      - name: Use token
        run: echo "Using token"
"""
        self.create_test_workflow("validation.yml", content)
        
        scanner = WorkflowSecretsScanner(str(self.workflows_dir))
        usages = scanner.scan_all_workflows()
        
        # Debug output
        
        # Should find the secret and mark it as required due to validation
        # Filter to just VERCEL_TOKEN usages
        vercel_usages = [u for u in usages if u.secret_name == "VERCEL_TOKEN"]
        self.assertGreater(len(vercel_usages), 0)
        # At least one should be marked as required
        self.assertTrue(any(u.is_required for u in vercel_usages))

    def test_conditional_secret_usage(self):
        """Test that secrets used in conditional steps might be optional"""
        content = """
name: Test Conditional
on: workflow_dispatch
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - name: Optional step
        if: secrets.VERCEL_TOKEN != ''
        env:
          VERCEL_TOKEN: ${{ secrets.VERCEL_TOKEN }}
        run: echo "Using Vercel"
"""
        self.create_test_workflow("conditional.yml", content)
        
        scanner = WorkflowSecretsScanner(str(self.workflows_dir))
        usages = scanner.scan_all_workflows()
        
        # Should find the secret - exact behavior might vary based on context analysis
        secret_names = {usage.secret_name for usage in usages}
        self.assertIn("VERCEL_TOKEN", secret_names)

    def test_report_generation(self):
        """Test that the scanner generates a proper report"""
        content = """
name: Multi Secret Test
on: workflow_dispatch
jobs:
  test:
    runs-on: ubuntu-latest
    env:
      SUPABASE_URL: ${{ secrets.SUPABASE_URL }}
      VERCEL_TOKEN: ${{ secrets.VERCEL_TOKEN }}
    steps:
      - name: Test
        run: echo "test"
"""
        self.create_test_workflow("multi.yml", content)
        
        scanner = WorkflowSecretsScanner(str(self.workflows_dir))
        usages = scanner.scan_all_workflows()
        
        # Test report generation
        report = scanner.generate_report()
        self.assertIn("Workflow Secrets Scanner Report", report)
        self.assertIn("SUPABASE_URL", report)
        self.assertIn("VERCEL_TOKEN", report)
        
        # Test unique secrets
        unique_secrets = scanner.get_unique_secrets()
        self.assertIn("SUPABASE_URL", unique_secrets)
        self.assertIn("VERCEL_TOKEN", unique_secrets)

    def test_no_secrets_found(self):
        """Test behavior when no secrets are found"""
        content = """
name: No Secrets
on: workflow_dispatch
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - name: Test
        run: echo "no secrets here"
"""
        self.create_test_workflow("nosecrets.yml", content)
        
        scanner = WorkflowSecretsScanner(str(self.workflows_dir))
        usages = scanner.scan_all_workflows()
        
        self.assertEqual(len(usages), 0)
        self.assertEqual(len(scanner.get_unique_secrets()), 0)

    def test_multiple_files(self):
        """Test scanning multiple workflow files"""
        # Create two workflow files with different secrets
        workflow1 = """
name: Workflow 1
env:
  SUPABASE_URL: ${{ secrets.SUPABASE_URL }}
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - run: echo "test"
"""
        
        workflow2 = """
name: Workflow 2
env:
  VERCEL_TOKEN: ${{ secrets.VERCEL_TOKEN }}
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - run: echo "test"
"""
        
        self.create_test_workflow("workflow1.yml", workflow1)
        self.create_test_workflow("workflow2.yml", workflow2)
        
        scanner = WorkflowSecretsScanner(str(self.workflows_dir))
        usages = scanner.scan_all_workflows()
        
        # Should find secrets from both files
        secret_names = {usage.secret_name for usage in usages}
        self.assertIn("SUPABASE_URL", secret_names)
        self.assertIn("VERCEL_TOKEN", secret_names)
        
        # Test grouping by file
        by_file = scanner.group_by_file()
        self.assertEqual(len(by_file), 2)


if __name__ == "__main__":
    print("=" * 60)
    print("Workflow Secrets Scanner Test Suite")
    print("=" * 60)
    unittest.main(verbosity=2)