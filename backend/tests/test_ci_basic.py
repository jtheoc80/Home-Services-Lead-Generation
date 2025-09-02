#!/usr/bin/env python3
"""
Simple test to verify the backend CI workflow is working.
This test doesn't require heavy dependencies and focuses on basic functionality.
"""

import unittest
import os
import sys

class TestBasicBackend(unittest.TestCase):
    """Basic backend tests for CI validation."""
    
    def test_python_version(self):
        """Test that we're running the correct Python version."""
        version = sys.version_info
        self.assertGreaterEqual(version.major, 3)
        self.assertGreaterEqual(version.minor, 8)
    
    def test_backend_directory(self):
        """Test that we're in the correct backend directory."""
        current_dir = os.getcwd()
        self.assertTrue(current_dir.endswith('backend'))
    
    def test_requirements_file_exists(self):
        """Test that requirements.txt exists."""
        self.assertTrue(os.path.exists('requirements.txt'))
    
    def test_can_import_basic_modules(self):
        """Test that we can import basic Python modules."""
        import json
        # These should always work
        self.assertTrue(True)

if __name__ == '__main__':
    unittest.main()