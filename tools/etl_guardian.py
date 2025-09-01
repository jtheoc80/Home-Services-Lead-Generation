#!/usr/bin/env python3
"""
ETL Guardian - Automatic ETL Workflow Fixer

This script automatically fixes common issues in the etl.yml workflow:
- Ensures mkdir step for logs/artifacts/data
- Makes ingestion step conditional
- Fixes summary to tail logs/etl_output.log
- Collapses duplicate artifact uploaders with stable globs
- Adds concurrency guard on jobs.etl
- Sets defaults.run.working-directory: permit_leads
"""

import argparse
import os
import sys
from pathlib import Path
from typing import Dict, Any, Optional
from ruamel.yaml import YAML


def load_etl_workflow() -> tuple[Path, Optional[Dict[str, Any]]]:
    """Load the etl.yml workflow file."""
    etl_path = Path(".github/workflows/etl.yml")
    
    if not etl_path.exists():
        print(f"❌ ETL workflow not found at {etl_path}")
        return etl_path, None
    
    yaml = YAML()
    yaml.preserve_quotes = True
    yaml.default_flow_style = False
    yaml.width = 4096
    
    try:
        with open(etl_path, 'r') as f:
            content = yaml.load(f)
        return etl_path, content
    except Exception as e:
        print(f"❌ Error loading ETL workflow: {e}")
        return etl_path, None


def ensure_mkdir_step(workflow: Dict[str, Any]) -> bool:
    """Ensure there's a mkdir step for logs/artifacts/data."""
    if 'jobs' not in workflow or 'etl' not in workflow['jobs']:
        return False
    
    steps = workflow['jobs']['etl'].get('steps', [])
    
    # Check if mkdir step exists
    for step in steps:
        if 'name' in step and 'ensure output dirs' in step['name'].lower():
            # Check if it creates the required directories
            run_script = step.get('run', '')
            if 'mkdir -p logs artifacts data' in run_script:
                print("✅ mkdir step already exists and is correct")
                return False
    
    # Find a good place to insert the mkdir step (after deps install)
    insert_index = 0
    for i, step in enumerate(steps):
        if 'name' in step and ('install deps' in step['name'].lower() or 'setup python' in step['name'].lower()):
            insert_index = i + 1
    
    # Add the mkdir step
    mkdir_step = {
        'name': 'Ensure output dirs',
        'run': 'mkdir -p logs artifacts data'
    }
    
    steps.insert(insert_index, mkdir_step)
    print("🔧 Added mkdir step for logs/artifacts/data")
    return True


def ensure_conditional_ingestion(workflow: Dict[str, Any]) -> bool:
    """Ensure ingestion step is conditional."""
    if 'jobs' not in workflow or 'etl' not in workflow['jobs']:
        return False
    
    steps = workflow['jobs']['etl'].get('steps', [])
    modified = False
    
    for step in steps:
        if 'name' in step and 'data ingestion' in step['name'].lower():
            # Check if it has the correct conditional
            current_if = step.get('if', '')
            expected_if = "${{ steps.scrape.outputs.record_count != '0' || inputs.force == true }}"
            
            if expected_if not in current_if:
                step['if'] = expected_if
                print("🔧 Fixed conditional ingestion step")
                modified = True
            else:
                print("✅ Ingestion step conditional is correct")
    
    return modified


def ensure_working_directory(workflow: Dict[str, Any]) -> bool:
    """Ensure defaults.run.working-directory is set to permit_leads."""
    if 'jobs' not in workflow or 'etl' not in workflow['jobs']:
        return False
    
    etl_job = workflow['jobs']['etl']
    
    # Check if defaults.run.working-directory exists
    if 'defaults' not in etl_job:
        etl_job['defaults'] = {}
    
    if 'run' not in etl_job['defaults']:
        etl_job['defaults']['run'] = {}
    
    if etl_job['defaults']['run'].get('working-directory') != 'permit_leads':
        etl_job['defaults']['run']['working-directory'] = 'permit_leads'
        print("🔧 Set working-directory to permit_leads")
        return True
    
    print("✅ Working directory already set correctly")
    return False


def ensure_concurrency_guard(workflow: Dict[str, Any]) -> bool:
    """Ensure concurrency guard is on jobs.etl."""
    if 'jobs' not in workflow or 'etl' not in workflow['jobs']:
        return False
    
    etl_job = workflow['jobs']['etl']
    
    # Check if concurrency exists and is correct
    expected_concurrency = {
        'group': 'nightly-etl',
        'cancel-in-progress': False
    }
    
    current_concurrency = etl_job.get('concurrency', {})
    
    if (current_concurrency.get('group') != expected_concurrency['group'] or 
        current_concurrency.get('cancel-in-progress') != expected_concurrency['cancel-in-progress']):
        
        etl_job['concurrency'] = expected_concurrency
        print("🔧 Added/fixed concurrency guard")
        return True
    
    print("✅ Concurrency guard already correct")
    return False


def collapse_artifact_uploaders(workflow: Dict[str, Any]) -> bool:
    """Collapse duplicate artifact uploaders into one with stable globs."""
    if 'jobs' not in workflow or 'etl' not in workflow['jobs']:
        return False
    
    steps = workflow['jobs']['etl'].get('steps', [])
    upload_steps = []
    other_steps = []
    
    # Separate upload steps from other steps
    for i, step in enumerate(steps):
        if step.get('uses', '').startswith('actions/upload-artifact'):
            upload_steps.append((i, step))
        else:
            other_steps.append((i, step))
    
    # If there's only one upload step, check if it's correct
    if len(upload_steps) <= 1:
        if upload_steps:
            step = upload_steps[0][1]
            expected_paths = [
                'permit_leads/artifacts/**/*.csv',
                'permit_leads/logs/**/*.log'
            ]
            
            with_config = step.get('with', {})
            current_path = with_config.get('path', '')
            
            # Check if paths match expected
            if isinstance(current_path, list):
                if set(current_path) == set(expected_paths):
                    print("✅ Artifact uploader already correct")
                    return False
            elif isinstance(current_path, str):
                if all(path in current_path for path in expected_paths):
                    print("✅ Artifact uploader already correct") 
                    return False
            
            # Fix the existing upload step
            with_config['path'] = expected_paths
            with_config['if-no-files-found'] = 'warn'
            print("🔧 Fixed artifact uploader paths")
            return True
        
        print("✅ No artifact uploaders to fix")
        return False
    
    # Multiple upload steps - collapse them
    # Remove all upload steps from the original steps list
    new_steps = [step for i, step in enumerate(steps) if i not in [idx for idx, _ in upload_steps]]
    
    # Create a single consolidated upload step
    consolidated_upload = {
        'name': 'Upload artifacts',
        'if': 'always()',
        'uses': 'actions/upload-artifact@v4',
        'with': {
            'name': 'nightly-etl-${{ github.run_id }}',
            'path': [
                'permit_leads/artifacts/**/*.csv',
                'permit_leads/logs/**/*.log'
            ],
            'if-no-files-found': 'warn',
            'retention-days': 14
        }
    }
    
    # Add it to the end
    new_steps.append(consolidated_upload)
    workflow['jobs']['etl']['steps'] = new_steps
    
    print(f"🔧 Collapsed {len(upload_steps)} artifact uploaders into one")
    return True


def fix_summary_tail(workflow: Dict[str, Any]) -> bool:
    """Fix summary to tail logs/etl_output.log."""
    if 'jobs' not in workflow or 'etl' not in workflow['jobs']:
        return False
    
    steps = workflow['jobs']['etl'].get('steps', [])
    
    for step in steps:
        if 'name' in step and 'summary' in step['name'].lower():
            run_script = step.get('run', '')
            
            # Check if it's tailing the correct log file
            if 'tail -n 25 logs/etl_output.log' in run_script:
                print("✅ Summary tail already correct")
                return False
            
            # Fix the tail command
            if 'tail' in run_script and 'etl_output.log' in run_script:
                # Replace existing tail command
                import re
                run_script = re.sub(
                    r'tail[^|]*etl_output\.log[^>]*',
                    'tail -n 25 logs/etl_output.log',
                    run_script
                )
                step['run'] = run_script
                print("🔧 Fixed summary tail command")
                return True
    
    print("ℹ️ No summary step found to fix")
    return False


def save_workflow(etl_path: Path, workflow: Dict[str, Any]) -> bool:
    """Save the updated workflow back to file."""
    try:
        yaml = YAML()
        yaml.preserve_quotes = True
        yaml.default_flow_style = False
        yaml.width = 4096
        
        with open(etl_path, 'w') as f:
            yaml.dump(workflow, f)
        
        return True
    except Exception as e:
        print(f"❌ Error saving workflow: {e}")
        return False


def main():
    """Main function to fix ETL workflow issues."""
    parser = argparse.ArgumentParser(description="ETL Guardian - Automatic ETL Workflow Fixer")
    parser.add_argument('--write', action='store_true', 
                       help='Write changes to the workflow file (default: dry-run)')
    args = parser.parse_args()
    
    print("🛡️ ETL Guardian: Checking and fixing etl.yml workflow...")
    
    # Change to repository root if we're in tools/
    if os.path.basename(os.getcwd()) == 'tools':
        os.chdir('..')
    
    etl_path, workflow = load_etl_workflow()
    
    if workflow is None:
        sys.exit(1)
    
    print(f"📁 Found ETL workflow at {etl_path}")
    
    # Apply fixes
    changes_made = False
    
    changes_made |= ensure_working_directory(workflow)
    changes_made |= ensure_concurrency_guard(workflow)
    changes_made |= ensure_mkdir_step(workflow)
    changes_made |= ensure_conditional_ingestion(workflow)
    changes_made |= collapse_artifact_uploaders(workflow)
    changes_made |= fix_summary_tail(workflow)
    
    if changes_made:
        if args.write:
            if save_workflow(etl_path, workflow):
                print("\n✅ ETL workflow updated successfully!")
                print("📝 Changes made to .github/workflows/etl.yml")
            else:
                print("\n❌ Failed to save workflow changes")
                sys.exit(1)
        else:
            print("\n📋 Changes would be made (use --write to apply)")
            print("💡 Run with --write flag to apply changes")
    else:
        print("\n✅ ETL workflow is already properly configured!")
        print("📋 No changes needed")
    
    sys.exit(0)


if __name__ == "__main__":
    main()