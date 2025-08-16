#!/usr/bin/env python3
"""
Test script to validate the Nixpacks configuration changes.
This simulates what Railway would do during deployment.
"""

import subprocess
import os
from pathlib import Path


def run_cmd(cmd, description):
    """Run a command and print results."""
    print(f"\n🔧 {description}")
    print(f"Command: {cmd}")
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, cwd=Path(__file__).parent)
        print(f"Exit code: {result.returncode}")
        if result.stdout:
            print(f"STDOUT:\n{result.stdout}")
        if result.stderr:
            print(f"STDERR:\n{result.stderr}")
        return result.returncode == 0
    except Exception as e:
        print(f"Error: {e}")
        return False


def test_nixpacks_install_simulation():
    """Simulate the nixpacks install phase."""
    print("🧪 SIMULATING NIXPACKS INSTALL PHASE")
    print("="*60)
    
    commands = [
        ("echo 'Python version check:'", "Debug: Python version check"),
        ("python3 --version || python --version", "Check available Python"),
        ("which python3 || which python", "Check Python location"),
        ("echo 'Installing Poetry with Python:'", "Debug: Poetry installation"),
        ("python3 -m pip install --upgrade pip poetry || python -m pip install --upgrade pip poetry", "Install Poetry"),
        ("echo 'Configuring Poetry:'", "Debug: Poetry configuration"),
        ("poetry config virtualenvs.create false", "Configure Poetry virtualenvs"),
        ("echo 'Poetry environment info:'", "Debug: Poetry environment"),
        ("poetry env info", "Show Poetry environment"),
        ("echo 'Installing dependencies:'", "Debug: Dependencies installation"),
        ("poetry install --without dev --no-interaction --no-ansi", "Install dependencies"),
    ]
    
    success_count = 0
    for cmd, desc in commands:
        if run_cmd(cmd, desc):
            success_count += 1
        else:
            print(f"❌ Failed: {desc}")
    
    print(f"\n🎯 SIMULATION RESULTS: {success_count}/{len(commands)} commands succeeded")
    return success_count == len(commands)


def test_python_version_constraints():
    """Test Python version constraint resolution."""
    print("\n🔍 TESTING PYTHON VERSION CONSTRAINT RESOLUTION")
    print("="*60)
    
    commands = [
        ("poetry run python -c \"import sys; print(f'Python version: {sys.version}')\"", "Check Python version in Poetry env"),
        ("poetry run python -c \"import scipy; print(f'Scipy version: {scipy.__version__}')\"", "Test scipy import"),
        ("poetry run python -c \"import sklearn; print(f'Scikit-learn version: {sklearn.__version__}')\"", "Test scikit-learn import"),
        ("poetry run python -c \"import numpy; print(f'Numpy version: {numpy.__version__}')\"", "Test numpy import"),
        ("poetry run python -c \"import pandas; print(f'Pandas version: {pandas.__version__}')\"", "Test pandas import"),
    ]
    
    success_count = 0
    for cmd, desc in commands:
        if run_cmd(cmd, desc):
            success_count += 1
        else:
            print(f"❌ Failed: {desc}")
    
    print(f"\n🎯 CONSTRAINT TEST RESULTS: {success_count}/{len(commands)} tests passed")
    return success_count == len(commands)


def main():
    """Run all tests."""
    print("🚀 NIXPACKS CONFIGURATION VALIDATION")
    print("="*60)
    print("Testing the updated nixpacks.toml configuration")
    print("to ensure Python 3.11 dependency resolution works correctly.")
    print("="*60)
    
    install_success = test_nixpacks_install_simulation()
    constraint_success = test_python_version_constraints()
    
    print("\n" + "="*60)
    print("🎯 FINAL RESULTS")
    print("="*60)
    
    if install_success and constraint_success:
        print("✅ ALL TESTS PASSED!")
        print("The nixpacks.toml configuration should work correctly on Railway.")
    else:
        print("❌ SOME TESTS FAILED!")
        print("The nixpacks.toml configuration may need further adjustments.")
        if not install_success:
            print("- Install simulation failed")
        if not constraint_success:
            print("- Python constraint resolution failed")


if __name__ == "__main__":
    main()