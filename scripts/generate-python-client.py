#!/usr/bin/env python3
"""
scripts/generate-python-client.py
Auto-generate Python client from OpenAPI spec using openapi-python-client
"""

import subprocess
import sys
from pathlib import Path


def main():
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    openapi_file = project_root / "openapi.yaml"
    output_dir = project_root / "backend" / "app" / "clients"

    print("🔧 Generating Python API client...")

    # Check if OpenAPI file exists
    if not openapi_file.exists():
        print(f"❌ Error: openapi.yaml not found at {openapi_file}")
        sys.exit(1)

    # Install openapi-python-client if not already installed
    try:
        import openapi_python_client

        print("✅ openapi-python-client is already installed")
    except ImportError:
        print("📦 Installing openapi-python-client...")
        subprocess.run(
            [sys.executable, "-m", "pip", "install", "openapi-python-client"],
            check=True,
        )

    # Create output directory if it doesn't exist
    output_dir.mkdir(parents=True, exist_ok=True)

    # Remove existing client if it exists
    client_dir = output_dir / "leadledderpro_client"
    if client_dir.exists():
        print("🗑️  Removing existing client...")
        import shutil

        shutil.rmtree(client_dir)

    # Generate Python client
    print("📝 Generating Python client...")
    try:
        subprocess.run(
            [
                "openapi-python-client",
                "generate",
                "--path",
                str(openapi_file),
                "--output-path",
                str(output_dir),
                "--config",
                str(script_dir / "openapi-python-config.yaml"),
            ],
            check=True,
            cwd=project_root,
        )
    except FileNotFoundError:
        # Fallback if config file doesn't exist
        subprocess.run(
            [
                "openapi-python-client",
                "generate",
                "--path",
                str(openapi_file),
                "--output-path",
                str(output_dir),
            ],
            check=True,
            cwd=project_root,
        )

    # Create a simple wrapper for easy imports
    wrapper_file = output_dir / "__init__.py"
    wrapper_content = '''"""
Auto-generated API client wrapper
Generated from openapi.yaml - do not edit manually
"""

try:
    from .leadledderpro_client import Client as LeadLedgerProClient
    from .leadledderpro_client.api import *
    from .leadledderpro_client.models import *
    
    __all__ = ["LeadLedgerProClient"]
    
except ImportError as e:
    # Fallback if client generation failed
    print(f"Warning: Could not import generated client: {e}")
    
    class LeadLedgerProClient:
        """Fallback client when generation fails"""
        def __init__(self, base_url: str = "http://localhost:8000"):
            self.base_url = base_url
            print("Warning: Using fallback client - generate proper client first")
'''

    with open(wrapper_file, "w") as f:
        f.write(wrapper_content)

    print("✅ Python API client generated successfully!")
    print(f"📁 Output directory: {output_dir}")
    print("📄 Files generated in leadledderpro_client/:")
    print("   - Client class with typed methods")
    print("   - Models for request/response objects")
    print("   - API modules for each endpoint group")
    print("")
    print("💡 Usage in your Python code:")
    print("   from backend.app.clients import LeadLedgerProClient")
    print("   client = LeadLedgerProClient(base_url='http://localhost:8000')")
    print("   health = client.get_health()")


if __name__ == "__main__":
    main()
