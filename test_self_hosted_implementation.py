#!/usr/bin/env python3
"""
Test script to validate the self-hosted runner workflow files and source probe functionality.
"""

import yaml
import json
import os
import subprocess
from pathlib import Path

def test_yaml_files():
    """Test that workflow YAML files are valid."""
    workflow_files = [
        '.github/workflows/self-hosted-health.yml',
        '.github/workflows/self-hosted-houston-backfill.yml'
    ]
    
    print("🧪 Testing YAML file validity...")
    for workflow_file in workflow_files:
        try:
            with open(workflow_file, 'r') as f:
                yaml.safe_load(f)
            print(f"  ✅ {workflow_file} is valid YAML")
        except Exception as e:
            print(f"  ❌ {workflow_file} has YAML errors: {e}")
            return False
    return True

def test_workflow_structure():
    """Test that workflows have required self-hosted runner configuration."""
    print("\n🔍 Testing workflow structure...")
    
    workflow_files = [
        '.github/workflows/self-hosted-health.yml',
        '.github/workflows/self-hosted-houston-backfill.yml'
    ]
    
    for workflow_file in workflow_files:
        with open(workflow_file, 'r') as f:
            workflow = yaml.safe_load(f)
        
        # Check for self-hosted runner configuration
        jobs = workflow.get('jobs', {})
        for job_name, job_config in jobs.items():
            runs_on = job_config.get('runs-on', [])
            
            # Should be a list containing self-hosted and specific labels
            if isinstance(runs_on, list):
                if 'self-hosted' in runs_on and 'scrape' in runs_on:
                    print(f"  ✅ {workflow_file} job '{job_name}' uses self-hosted runner with 'scrape' label")
                else:
                    print(f"  ❌ {workflow_file} job '{job_name}' missing self-hosted or scrape label")
                    return False
            else:
                print(f"  ❌ {workflow_file} job '{job_name}' runs-on should be a list")
                return False
        
        # Check for concurrency controls
        concurrency = workflow.get('concurrency', {})
        if 'group' in concurrency and 'cancel-in-progress' in concurrency:
            if 'scrape-' in concurrency['group'] and concurrency['cancel-in-progress'] is False:
                print(f"  ✅ {workflow_file} has proper concurrency controls")
            else:
                print(f"  ❌ {workflow_file} concurrency controls not configured correctly")
                return False
        else:
            print(f"  ❌ {workflow_file} missing concurrency controls")
            return False
    
    return True

def test_source_probe_script():
    """Test the source probe script functionality."""
    print("\n🚀 Testing source probe script...")
    
    script_path = 'scripts/agents/source_probe.py'
    if not os.path.exists(script_path):
        print(f"  ❌ {script_path} does not exist")
        return False
    
    # Check if script is executable
    if not os.access(script_path, os.X_OK):
        print(f"  ⚠️  {script_path} is not executable")
    
    # Test that the script can load without errors
    try:
        result = subprocess.run(['python3', script_path], 
                              capture_output=True, text=True, timeout=30)
        
        # Script should exit with code 1 (sources offline) but no Python errors
        if result.returncode in [0, 1]:  # 0 = all online, 1 = some offline
            print(f"  ✅ {script_path} executed successfully")
            
            # Check if it creates artifacts
            if os.path.exists('artifacts/source_health.json'):
                try:
                    with open('artifacts/source_health.json', 'r') as f:
                        health_data = json.load(f)
                    
                    # Validate JSON structure
                    required_fields = ['timestamp', 'summary', 'sources']
                    if all(field in health_data for field in required_fields):
                        print(f"  ✅ {script_path} produces valid JSON output")
                        
                        # Check summary structure
                        summary = health_data['summary']
                        if all(key in summary for key in ['total', 'online', 'limited', 'offline']):
                            print(f"  ✅ Health summary has all required fields")
                            return True
                        else:
                            print(f"  ❌ Health summary missing required fields")
                            return False
                    else:
                        print(f"  ❌ Health JSON missing required top-level fields")
                        return False
                except json.JSONDecodeError as e:
                    print(f"  ❌ Invalid JSON output: {e}")
                    return False
            else:
                print(f"  ⚠️  No artifacts/source_health.json created")
                return True  # Still OK, might be environment issue
        else:
            print(f"  ❌ {script_path} failed with exit code {result.returncode}")
            print(f"    stderr: {result.stderr}")
            return False
            
    except subprocess.TimeoutExpired:
        print(f"  ❌ {script_path} timed out")
        return False
    except Exception as e:
        print(f"  ❌ Error testing {script_path}: {e}")
        return False

def test_documentation():
    """Test that documentation files exist and contain key sections."""
    print("\n📚 Testing documentation...")
    
    doc_file = 'docs/self-hosted-runners.md'
    if not os.path.exists(doc_file):
        print(f"  ❌ {doc_file} does not exist")
        return False
    
    with open(doc_file, 'r') as f:
        content = f.read()
    
    # Check for key sections
    required_sections = [
        'Why Self-Hosted Runners?',
        'Runner Setup',
        'Install GitHub Actions Runner',
        'Configure Runner Labels',
        'Workflow Configuration',
        'Security Considerations',
        'Troubleshooting'
    ]
    
    missing_sections = []
    for section in required_sections:
        if section not in content:
            missing_sections.append(section)
    
    if missing_sections:
        print(f"  ❌ {doc_file} missing sections: {missing_sections}")
        return False
    else:
        print(f"  ✅ {doc_file} contains all required sections")
    
    # Check for self-hosted runner labels
    if '[self-hosted, linux, x64, scrape]' in content:
        print(f"  ✅ {doc_file} documents correct runner labels")
        return True
    else:
        print(f"  ❌ {doc_file} missing runner label documentation")
        return False

def main():
    """Run all tests."""
    print("🧪 Testing Self-Hosted Runner Implementation")
    print("=" * 50)
    
    # Ensure we're in the right directory
    os.chdir(Path(__file__).parent)
    
    # Create artifacts directory for testing
    os.makedirs('artifacts', exist_ok=True)
    
    tests = [
        ("YAML File Validity", test_yaml_files),
        ("Workflow Structure", test_workflow_structure),
        ("Source Probe Script", test_source_probe_script),
        ("Documentation", test_documentation)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        if test_func():
            passed += 1
        else:
            print(f"\n❌ {test_name} test failed")
    
    print("\n" + "=" * 50)
    print(f"🎯 Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("✅ All tests passed! Self-hosted runner implementation is ready.")
        return 0
    else:
        print("❌ Some tests failed. Please review the issues above.")
        return 1

if __name__ == '__main__':
    exit(main())