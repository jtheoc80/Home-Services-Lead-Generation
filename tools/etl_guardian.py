#!/usr/bin/env python3
"""
ETL Guardian - Repository Policy Check

This script exits non-zero if it detects changes outside allowed files.

ALLOWED PATHS:
- permit_leads/          - Core ETL pipeline code
- scripts/               - ETL scripts and tooling
- config/                - Configuration files (registry.yaml, sources_tx.yaml)
- backend/               - Backend API and workers
- sql/                   - Database migrations and setup scripts
- docs/                  - Documentation files
- tools/                 - Development tools and utilities
- *.md                   - Root-level documentation
- *.yaml, *.yml          - Root-level configuration
- *.json                 - Root-level configuration (package.json, etc.)
- *.py                   - Root-level Python scripts
- *.sql                  - Root-level SQL scripts
- .github/               - GitHub workflows and configuration
- requirements.txt       - Python dependencies
- pyproject.toml         - Python project configuration
- poetry.lock            - Python dependency lock file
- package*.json          - Node.js dependencies
"""

import sys
import subprocess
from pathlib import Path
from typing import List


def get_changed_files() -> List[str]:
    """
    Get list of changed files using git diff.

    Returns list of file paths that have been modified, added, or deleted.
    """
    try:
        # Get staged changes
        result_staged = subprocess.run(
            ["git", "diff", "--cached", "--name-only"],
            capture_output=True,
            text=True,
            check=True,
        )

        # Get unstaged changes
        result_unstaged = subprocess.run(
            ["git", "diff", "--name-only"], capture_output=True, text=True, check=True
        )

        # Get untracked files
        result_untracked = subprocess.run(
            ["git", "ls-files", "--others", "--exclude-standard"],
            capture_output=True,
            text=True,
            check=True,
        )

        changed_files = set()

        # Combine all changes
        for result in [result_staged, result_unstaged, result_untracked]:
            if result.stdout.strip():
                changed_files.update(result.stdout.strip().split("\n"))

        return sorted(list(changed_files))

    except subprocess.CalledProcessError as e:
        print(f"Error getting changed files: {e}")
        return []


def is_path_allowed(file_path: str) -> bool:
    """
    Check if a file path is within allowed directories or matches allowed patterns.

    Args:
        file_path: Path to check

    Returns:
        True if path is allowed, False otherwise
    """
    path = Path(file_path)

    # Convert to string for easier matching
    path_str = str(path)

    # Allowed directory prefixes
    allowed_dirs = [
        "permit_leads/",
        "scripts/",
        "config/",
        "backend/",
        "sql/",
        "docs/",
        "tools/",
        ".github/",
    ]

    # Check if path starts with any allowed directory
    for allowed_dir in allowed_dirs:
        if path_str.startswith(allowed_dir):
            return True

    # Allowed root-level patterns
    allowed_root_patterns = [
        # Documentation
        "*.md",
        # Configuration files
        "*.yaml",
        "*.yml",
        "*.json",
        # Python files
        "*.py",
        # SQL files
        "*.sql",
        # Dependency files
        "requirements.txt",
        "pyproject.toml",
        "poetry.lock",
        "package.json",
        "package-lock.json",
        # Other configuration
        ".gitignore",
        ".env.example",
        ".nvmrc",
        "Makefile",
        "Procfile",
        "nixpacks.toml",
        "railway.json",
        "vercel.json",
        "openapi.yaml",
        "openapitools.json",
        "playwright.config.ts",
        "setup.py",
        "setup.sh",
    ]

    # Check if it's a root-level file matching allowed patterns
    if "/" not in path_str:  # Root-level file
        for pattern in allowed_root_patterns:
            if pattern.startswith("*"):
                extension = pattern[1:]  # Remove the *
                if path_str.endswith(extension):
                    return True
            elif path_str == pattern:
                return True

    return False


def main():
    """
    Main function to check for changes outside allowed paths.

    Exits with code 0 if all changes are in allowed paths.
    Exits with code 1 if changes are detected outside allowed paths.
    """
    print("🔍 ETL Guardian: Checking for changes outside allowed paths...")

    changed_files = get_changed_files()

    if not changed_files:
        print("✅ No changes detected.")
        sys.exit(0)

    print(f"📁 Found {len(changed_files)} changed file(s):")

    disallowed_files = []
    allowed_files = []

    for file_path in changed_files:
        if is_path_allowed(file_path):
            allowed_files.append(file_path)
            print(f"  ✅ {file_path}")
        else:
            disallowed_files.append(file_path)
            print(f"  ❌ {file_path}")

    if disallowed_files:
        print(
            f"\n🚫 ERROR: {len(disallowed_files)} file(s) changed outside allowed paths:"
        )
        for file_path in disallowed_files:
            print(f"  - {file_path}")

        print("\n📋 Allowed paths:")
        print("  - permit_leads/          - Core ETL pipeline code")
        print("  - scripts/               - ETL scripts and tooling")
        print("  - config/                - Configuration files")
        print("  - backend/               - Backend API and workers")
        print("  - sql/                   - Database migrations")
        print("  - docs/                  - Documentation")
        print("  - tools/                 - Development tools")
        print("  - .github/               - GitHub workflows")
        print("  - *.md, *.yaml, *.json   - Root-level config/docs")
        print("  - *.py, *.sql            - Root-level scripts")
        print("  - requirements.txt       - Dependencies")

        sys.exit(1)

    print(f"\n✅ All {len(allowed_files)} changed file(s) are in allowed paths.")
    sys.exit(0)


if __name__ == "__main__":
    main()
