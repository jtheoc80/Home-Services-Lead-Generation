#!/usr/bin/env python3
"""
Setup script for Home Services Lead Generation platform.
Installs dependencies for both permit_leads and backend components.
"""

import subprocess
import sys
import os
from pathlib import Path


def run_command(command, description):
    """Run a command and handle errors."""
    print(f"\n{description}...")
    print(f"Running: {' '.join(command)}")

    try:
        result = subprocess.run(command, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed successfully")
        if result.stdout:
            print(f"Output: {result.stdout.strip()}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed with exit code {e.returncode}")
        if e.stdout:
            print(f"stdout: {e.stdout}")
        if e.stderr:
            print(f"stderr: {e.stderr}")
        return False


def check_python_version():
    """Check if Python version is 3.11 or higher."""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 11):
        print(
            f"❌ Python 3.11+ required, but found Python {version.major}.{version.minor}"
        )
        return False
    print(f"✅ Python {version.major}.{version.minor}.{version.micro} is compatible")
    return True


def check_files_exist():
    """Check if requirements files exist."""
    root_dir = Path(__file__).parent
    permit_req = root_dir / "permit_leads" / "requirements.txt"
    backend_req = root_dir / "backend" / "requirements.txt"

    if not permit_req.exists():
        print(f"❌ Requirements file not found: {permit_req}")
        return False

    if not backend_req.exists():
        print(f"❌ Requirements file not found: {backend_req}")
        return False

    print("✅ Requirements files found")
    return True


def main():
    """Main setup function."""
    print("🏠 Home Services Lead Generation - Setup Script")
    print("=" * 50)

    # Check prerequisites
    if not check_python_version():
        sys.exit(1)

    if not check_files_exist():
        sys.exit(1)

    # Change to project root directory
    root_dir = Path(__file__).parent
    os.chdir(root_dir)
    print(f"Working directory: {root_dir}")

    # Install permit_leads requirements
    success1 = run_command(
        [sys.executable, "-m", "pip", "install", "-r", "permit_leads/requirements.txt"],
        "Installing permit_leads dependencies",
    )

    # Install backend requirements
    success2 = run_command(
        [sys.executable, "-m", "pip", "install", "-r", "backend/requirements.txt"],
        "Installing backend dependencies",
    )

    # Summary
    print("\n" + "=" * 50)
    if success1 and success2:
        print("🎉 Setup completed successfully!")
        print("\nNext steps:")
        print("1. Configure environment variables:")
        print("   - Copy backend/.env.example to backend/.env")
        print("   - Copy frontend/.env.example to frontend/.env.local")
        print("2. Setup database (see README.md)")
        print("3. Install frontend dependencies: cd frontend && npm install")
    else:
        print("❌ Setup failed. Please check the errors above.")
        sys.exit(1)


if __name__ == "__main__":
    main()
