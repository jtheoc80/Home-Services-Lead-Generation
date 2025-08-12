#!/usr/bin/env python3
"""
Extract OpenAPI specification from FastAPI app.
This script should be run when the API changes to update openapi.yaml.
"""

import sys
import os
import yaml
from pathlib import Path

# Get the repository root directory
repo_root = Path(__file__).parent.parent
backend_dir = repo_root / "backend"
sys.path.insert(0, str(backend_dir))

# Set minimal environment variables
os.environ.setdefault('CORS_ALLOWED_ORIGINS', 'http://localhost:3000')

try:
    # Try to import the real FastAPI app
    from main import app
    
    print("✅ Successfully imported FastAPI app")
    
    # Extract OpenAPI spec
    openapi_spec = app.openapi()
    
    # Convert to YAML format
    yaml_content = yaml.dump(openapi_spec, default_flow_style=False, sort_keys=False, allow_unicode=True)
    
    # Write to openapi.yaml in repository root
    output_path = repo_root / "openapi.yaml"
    with open(output_path, 'w') as f:
        f.write(yaml_content)
    
    print(f"✅ OpenAPI specification updated: {output_path}")
    print(f"📊 Spec contains {len(openapi_spec.get('paths', {}))} endpoints")
    
    # List endpoints for verification
    print("\n📝 API Endpoints:")
    for path, methods in openapi_spec.get('paths', {}).items():
        for method in methods.keys():
            if method.upper() in ['GET', 'POST', 'PUT', 'DELETE', 'PATCH']:
                operation = methods[method]
                summary = operation.get('summary', 'No summary')
                print(f"  {method.upper()} {path} - {summary}")

except ImportError as e:
    print(f"❌ Failed to import FastAPI app: {e}")
    print("💡 Make sure you have all dependencies installed:")
    print("   pip install -r backend/requirements.txt")
    sys.exit(1)
except Exception as e:
    print(f"❌ Error extracting OpenAPI spec: {e}")
    sys.exit(1)