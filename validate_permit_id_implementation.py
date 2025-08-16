#!/usr/bin/env python3
"""
Validation script for permit_id migration completeness.

This script validates that the existing migration file contains all the 
required elements mentioned in the problem statement.
"""

import re
from pathlib import Path

def validate_migration_file():
    """Validate that the migration file has all required components."""
    
    migration_path = Path("supabase/migrations/align_repo_supabase.sql")
    
    if not migration_path.exists():
        raise FileNotFoundError(f"Migration file not found: {migration_path}")
    
    content = migration_path.read_text()
    
    # Required checks based on problem statement
    checks = [
        {
            "name": "Add permit_id column",
            "pattern": r"ADD COLUMN permit_id TEXT",
            "required": True
        },
        {
            "name": "Backfill permit_id from existing data", 
            "pattern": r"UPDATE.*permits.*SET permit_id.*COALESCE",
            "required": True
        },
        {
            "name": "Unique index on (source, permit_id)",
            "pattern": r"CREATE UNIQUE INDEX.*permits.*source.*permit_id",
            "required": True
        },
        {
            "name": "upsert_permit function with permit_id derivation",
            "pattern": r"CREATE OR REPLACE FUNCTION.*upsert_permit.*JSONB",
            "required": True
        },
        {
            "name": "permit_id derivation logic in upsert_permit",
            "pattern": r"canonical_permit_id.*COALESCE.*permit_id.*permit_number.*source_record_id",
            "required": True
        },
        {
            "name": "Enhanced applicant/owner field mapping",
            "pattern": r"applicant.*COALESCE.*applicant.*applicant_name",
            "required": True
        },
        {
            "name": "Enhanced owner field mapping", 
            "pattern": r"owner.*COALESCE.*owner.*owner_name",
            "required": True
        },
        {
            "name": "Support for valuation/value field mapping",
            "pattern": r"valuation.*value.*NUMERIC",
            "required": True
        }
    ]
    
    print("🔍 Validating migration file for permit_id implementation...")
    print("=" * 60)
    
    passed = 0
    failed = 0
    
    for check in checks:
        pattern = check["pattern"]
        name = check["name"]
        required = check["required"]
        
        if re.search(pattern, content, re.IGNORECASE | re.DOTALL):
            print(f"✅ {name}")
            passed += 1
        else:
            if required:
                print(f"❌ {name} - REQUIRED BUT MISSING")
                failed += 1
            else:
                print(f"⚠️  {name} - optional, not found")
    
    print("=" * 60)
    
    if failed == 0:
        print(f"🎉 Migration validation PASSED! ({passed} checks passed)")
        return True
    else:
        print(f"💥 Migration validation FAILED! ({failed} required checks failed, {passed} passed)")
        return False

def validate_field_aliases():
    """Validate that field aliases include permit_id mapping."""
    
    aliases_path = Path("normalizers/field_aliases.py")
    
    if not aliases_path.exists():
        print("⚠️  Field aliases file not found, skipping validation")
        return True
    
    content = aliases_path.read_text()
    
    # Check for permit_id aliases
    if '"permit_id"' in content and 'permit_number' in content:
        print("✅ Field aliases include permit_id mapping")
        return True
    else:
        print("❌ Field aliases missing permit_id mapping")
        return False

def validate_normalizer_usage():
    """Validate that normalizer includes permit_id in output."""
    
    normalizer_path = Path("normalizers/permits.py")
    
    if not normalizer_path.exists():
        print("⚠️  Normalizer file not found, skipping validation")
        return True
    
    content = normalizer_path.read_text()
    
    # Check for permit_id in canonical record
    if "canonical['permit_id']" in content:
        print("✅ Normalizer includes permit_id in canonical record")
        return True
    else:
        print("❌ Normalizer missing permit_id in canonical record")
        return False

def validate_api_endpoint():
    """Validate that selftest endpoint was added."""
    
    api_path = Path("backend/main.py")
    
    if not api_path.exists():
        print("⚠️  API file not found, skipping validation")
        return True
    
    content = api_path.read_text()
    
    # Check for selftest endpoint
    if "/api/permits/selftest" in content:
        print("✅ Selftest API endpoint added")
        return True
    else:
        print("❌ Selftest API endpoint missing")
        return False

if __name__ == "__main__":
    print("🧪 Validating permit_id implementation completeness")
    print("=" * 60)
    
    all_passed = True
    
    try:
        # Run all validations
        if not validate_migration_file():
            all_passed = False
            
        if not validate_field_aliases():
            all_passed = False
            
        if not validate_normalizer_usage():
            all_passed = False
            
        if not validate_api_endpoint():
            all_passed = False
        
        print("=" * 60)
        
        if all_passed:
            print("🎉 ALL VALIDATIONS PASSED!")
            print("\nNext steps:")
            print("1. Run the migration: supabase/migrations/align_repo_supabase.sql")
            print("2. Test with: curl http://localhost:8000/api/permits/selftest")
            print("3. Verify with: SELECT source, permit_id, permit_number FROM public.permits WHERE source='selftest'")
        else:
            print("💥 SOME VALIDATIONS FAILED!")
            print("\nPlease review the failed checks above before proceeding.")
            exit(1)
            
    except Exception as e:
        print(f"❌ Validation error: {e}")
        exit(1)