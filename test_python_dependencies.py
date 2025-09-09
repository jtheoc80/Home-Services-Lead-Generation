#!/usr/bin/env python3
"""
Test script to validate Python dependencies for Railway deployment.

This script verifies that the core Python dependencies can be imported
and are compatible with the specified Python version constraints.
"""

import sys
import subprocess
from pathlib import Path


def test_python_version():
    """Test that Python version meets requirements."""
    print("🧪 Testing Python version requirements...")

    version_info = sys.version_info
    print(
        f"Current Python version: {version_info.major}.{version_info.minor}.{version_info.micro}"
    )

    # Check minimum Python 3.10 requirement
    if version_info < (3, 10):
        print("❌ Python version too old. Requires Python >= 3.10")
        return False
    elif version_info >= (4, 0):
        print("❌ Python version too new. Requires Python < 4.0")
        return False
    else:
        print("✅ Python version meets requirements (>=3.10, <4.0)")
        return True


def test_core_dependencies():
    """Test that core ML dependencies can be imported."""
    print("\n🧪 Testing core ML dependencies...")

    dependencies = [
        ("numpy", "numpy"),
        ("scipy", "scipy"),
        ("sklearn", "sklearn"),
        ("pandas", "pandas"),
    ]

    all_passed = True

    for dep_name, import_name in dependencies:
        try:
            module = __import__(import_name)
            version = getattr(module, "__version__", "unknown")
            print(f"✅ {dep_name} {version}")
        except ImportError as e:
            print(f"❌ {dep_name}: {e}")
            all_passed = False

    return all_passed


def test_fastapi_dependencies():
    """Test that FastAPI dependencies can be imported."""
    print("\n🧪 Testing FastAPI dependencies...")

    dependencies = [
        "fastapi",
        "uvicorn",
        "pydantic",
        "pydantic_settings",
    ]

    all_passed = True

    for dep_name in dependencies:
        try:
            module = __import__(dep_name)
            version = getattr(module, "__version__", "unknown")
            print(f"✅ {dep_name} {version}")
        except ImportError as e:
            print(f"❌ {dep_name}: {e}")
            all_passed = False

    return all_passed


def test_poetry_lock_consistency():
    """Test that poetry.lock is consistent with pyproject.toml."""
    print("\n🧪 Testing Poetry lock file consistency...")

    try:
        result = subprocess.run(
            ["poetry", "check", "--lock"],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent,
        )

        if result.returncode == 0:
            print("✅ Poetry configuration is valid")
            return True
        else:
            print(f"❌ Poetry check failed: {result.stderr}")
            return False
    except FileNotFoundError:
        print("⚠️  Poetry not found, skipping lock file check")
        return True
    except Exception as e:
        print(f"❌ Error checking Poetry: {e}")
        return False


def main():
    """Run all dependency tests."""
    print("🔍 Running Python dependency validation tests...\n")

    tests = [
        ("Python Version", test_python_version),
        ("Core ML Dependencies", test_core_dependencies),
        ("FastAPI Dependencies", test_fastapi_dependencies),
        ("Poetry Lock Consistency", test_poetry_lock_consistency),
    ]

    results = []
    for test_name, test_func in tests:
        print(f"--- {test_name} ---")
        result = test_func()
        results.append((test_name, result))

    print("\n" + "=" * 50)
    print("🎯 DEPENDENCY TEST SUMMARY")
    print("=" * 50)

    all_passed = True
    for test_name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status} - {test_name}")
        if not passed:
            all_passed = False

    print("\n" + "=" * 50)
    if all_passed:
        print("🎉 ALL DEPENDENCY TESTS PASSED! Ready for Railway deployment.")
    else:
        print("⚠️  Some dependency tests failed. Please review the issues above.")
    print("=" * 50)

    return 0 if all_passed else 1


if __name__ == "__main__":
    exit(main())
