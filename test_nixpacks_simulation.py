#!/usr/bin/env python3
"""
Test script to simulate the Nixpacks environment and validate Python 3.11 setup.
This helps debug the Railway deployment issue before actual deployment.
"""

import subprocess
import sys
import os
from pathlib import Path


def run_command(cmd, description, check=True):
    """Run a command and return the result."""
    print(f"\n🔧 {description}")
    print(f"Running: {cmd}")
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent
        )
        
        if result.stdout:
            print(f"STDOUT:\n{result.stdout}")
        if result.stderr:
            print(f"STDERR:\n{result.stderr}")
            
        if check and result.returncode != 0:
            print(f"❌ Command failed with exit code {result.returncode}")
            return False
        else:
            print(f"✅ Command completed with exit code {result.returncode}")
            return True
            
    except Exception as e:
        print(f"❌ Error running command: {e}")
        return False


def test_python_version_detection():
    """Test Python version detection similar to what Poetry does."""
    print("\n" + "="*60)
    print("🐍 TESTING PYTHON VERSION DETECTION")
    print("="*60)
    
    # Test various Python commands
    commands = [
        ("python --version", "System Python version"),
        ("python3 --version", "Python3 version"),
        ("which python", "Python location"),
        ("which python3", "Python3 location"),
    ]
    
    for cmd, desc in commands:
        run_command(cmd, desc, check=False)


def test_poetry_configuration():
    """Test Poetry configuration and dependency resolution."""
    print("\n" + "="*60)
    print("📦 TESTING POETRY CONFIGURATION")
    print("="*60)
    
    # Test Poetry commands
    commands = [
        ("poetry --version", "Poetry version"),
        ("poetry env info", "Poetry environment info"),
        ("poetry config --list", "Poetry configuration"),
        ("poetry check", "Poetry project validation"),
        ("poetry show --tree", "Dependency tree (if installed)"),
    ]
    
    for cmd, desc in commands:
        run_command(cmd, desc, check=False)


def test_dependency_compatibility():
    """Test that dependencies are compatible with current Python version."""
    print("\n" + "="*60)
    print("🔍 TESTING DEPENDENCY COMPATIBILITY")
    print("="*60)
    
    # Test specific dependency resolution
    commands = [
        ("poetry show scikit-learn", "scikit-learn package info"),
        ("poetry show scipy", "scipy package info"),
        ("poetry show numpy", "numpy package info"),
    ]
    
    for cmd, desc in commands:
        run_command(cmd, desc, check=False)


def main():
    """Run all tests."""
    print("🧪 NIXPACKS ENVIRONMENT SIMULATION TEST")
    print("="*60)
    print("This script simulates the Railway/Nixpacks environment")
    print("to debug Python 3.11 dependency resolution issues.")
    print("="*60)
    
    test_python_version_detection()
    test_poetry_configuration() 
    test_dependency_compatibility()
    
    print("\n" + "="*60)
    print("🎯 SIMULATION COMPLETE")
    print("="*60)
    print("Review the output above to identify any potential issues")
    print("that might occur in the Railway/Nixpacks environment.")


if __name__ == "__main__":
    main()