#!/usr/bin/env python3
"""
Harris County permit scraper script
Wrapper script for permit_leads jurisdiction-based scraping
"""

import argparse
import sys
import os
import subprocess

def main():
    parser = argparse.ArgumentParser(description='Harris County permit scraper')
    parser.add_argument('--days', type=int, default=1, help='Number of days to look back')
    parser.add_argument('--sample', action='store_true', help='Use sample data')
    args = parser.parse_args()
    
    # Set environment variables
    if args.sample:
        os.environ['SAMPLE_DATA'] = '1'
    else:
        os.environ['SAMPLE_DATA'] = '0'
    
    # Change to permit_leads directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    permit_leads_dir = os.path.join(script_dir, '..', 'permit_leads')
    os.chdir(permit_leads_dir)
    
    # Run the jurisdiction-based scraper
    cmd = [
        'python', '-m', 'permit_leads', 'scrape',
        '--jurisdiction', 'tx-harris',
        '--days', str(args.days),
        '--formats', 'csv', 'sqlite', 'jsonl',
        '--verbose',
        '--retries', '5'
    ]
    
    print(f"Running Harris County scraper with command: {' '.join(cmd)}")
    result = subprocess.run(cmd)
    sys.exit(result.returncode)

if __name__ == '__main__':
    main()