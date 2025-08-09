#!/usr/bin/env python3
"""
Test script to verify staging environment configuration.
"""
import os
import sys
import json
from pathlib import Path

# Add backend to Python path
backend_dir = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_dir))

def test_staging_configuration():
    """Test staging environment configuration."""
    print("🧪 Testing Staging Environment Configuration")
    print("=" * 50)
    
    # Set staging environment
    os.environ['APP_ENV'] = 'staging'
    
    try:
        from app.settings import settings
        from app.health_api import health_api
        
        # Test settings
        print(f"✓ Environment: {settings.app_env}")
        print(f"✓ Is staging: {settings.is_staging}")
        print(f"✓ Debug mode: {settings.debug}")
        print(f"✓ Database URL: {settings.database_url[:30]}...")
        print(f"✓ Redis URL: {settings.redis_url[:30]}...")
        
        # Test health API
        status = health_api.handle_health_check()
        print(f"✓ Health check response: {json.dumps(status, indent=2)}")
        
        # Test staging-specific settings
        assert settings.app_env == 'staging'
        assert settings.is_staging == True
        assert settings.is_production == False
        
        print("\n🎉 Staging configuration test passed!")
        return True
        
    except Exception as e:
        print(f"\n❌ Staging configuration test failed: {e}")
        return False

def test_migration_script():
    """Test migration script."""
    print("\n🧪 Testing Migration Script")
    print("=" * 50)
    
    try:
        import subprocess
        result = subprocess.run([
            sys.executable, 'scripts/migrate.py', '--dry-run'
        ], capture_output=True, text=True, cwd=Path(__file__).parent.parent)
        
        if result.returncode == 0:
            print("✓ Migration script dry-run passed")
            print(f"✓ Output: {result.stdout.split('Migration completed')[0].strip()}")
            return True
        else:
            print(f"❌ Migration script failed: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ Migration test failed: {e}")
        return False

def test_frontend_config():
    """Test frontend configuration."""
    print("\n🧪 Testing Frontend Configuration")
    print("=" * 50)
    
    try:
        # Set staging environment for frontend
        os.environ['NEXT_PUBLIC_ENV'] = 'staging'
        
        frontend_dir = Path(__file__).parent.parent / "frontend"
        config_file = frontend_dir / "lib" / "config.ts"
        
        assert config_file.exists(), "Frontend config file missing"
        print("✓ Frontend config file exists")
        
        config_content = config_file.read_text()
        assert 'staging' in config_content, "Staging configuration missing"
        assert 'showStagingBanner' in config_content, "Staging banner config missing"
        print("✓ Frontend config includes staging settings")
        
        # Check staging banner component
        banner_file = frontend_dir / "components" / "StagingBanner.tsx"
        assert banner_file.exists(), "Staging banner component missing"
        print("✓ Staging banner component exists")
        
        return True
        
    except Exception as e:
        print(f"❌ Frontend config test failed: {e}")
        return False

def test_makefile_targets():
    """Test Makefile staging targets."""
    print("\n🧪 Testing Makefile Targets")
    print("=" * 50)
    
    try:
        import subprocess
        
        # Test help target
        result = subprocess.run(['make', 'help'], capture_output=True, text=True,
                               cwd=Path(__file__).parent.parent)
        
        if result.returncode == 0:
            assert 'stage-migrate' in result.stdout, "stage-migrate target missing"
            assert 'stage-seed' in result.stdout, "stage-seed target missing"
            print("✓ Makefile includes staging targets")
            return True
        else:
            print(f"❌ Makefile test failed: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ Makefile test failed: {e}")
        return False

def main():
    """Run all staging tests."""
    print("🚀 LeadLedgerPro Staging Environment Test Suite")
    print("=" * 60)
    
    tests = [
        test_staging_configuration,
        test_migration_script,
        test_frontend_config,
        test_makefile_targets,
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"❌ Test {test.__name__} crashed: {e}")
            results.append(False)
    
    print("\n" + "=" * 60)
    print("🎯 TEST SUMMARY")
    print("=" * 60)
    
    passed = sum(results)
    total = len(results)
    
    print(f"Tests passed: {passed}/{total}")
    
    if passed == total:
        print("🎉 All staging environment tests passed!")
        print("\nStaging environment is ready for use:")
        print("1. Set APP_ENV=staging and NEXT_PUBLIC_ENV=staging")
        print("2. Configure staging database and Redis URLs")
        print("3. Run 'make stage-migrate' to set up database")
        print("4. Run 'make stage-seed' to add demo data")
        print("5. Run 'make dev' to start development servers")
        return 0
    else:
        print("❌ Some staging environment tests failed.")
        print("Please fix the issues above before using staging environment.")
        return 1

if __name__ == "__main__":
    sys.exit(main())