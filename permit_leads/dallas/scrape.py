"""
Dallas County permit scraper implementation
Uses the jurisdiction-based scraping system
"""

import subprocess
import sys
import os
from pathlib import Path

def run_scraper(days=1, sample_data=False, formats=None):
    """
    Run Dallas County permit scraper
    
    Args:
        days (int): Number of days to look back
        sample_data (bool): Whether to use sample data
        formats (list): Output formats
    """
    if formats is None:
        formats = ['csv', 'sqlite', 'jsonl']
    
    # Set environment variables
    if sample_data:
        os.environ['SAMPLE_DATA'] = '1'
    else:
        os.environ['SAMPLE_DATA'] = '0'
    
    # Get permit_leads directory
    current_dir = Path(__file__).parent.parent
    os.chdir(current_dir)
    
    # Build command
    cmd = [
        'python', '-m', 'permit_leads', 'scrape',
        '--jurisdiction', 'tx-dallas',
        '--days', str(days),
        '--formats'] + formats + [
        '--verbose',
        '--retries', '5'
    ]
    
    print(f"Running Dallas County scraper: {' '.join(cmd)}")
    result = subprocess.run(cmd)
    return result.returncode

def main():
    """Main entry point for command line usage"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Dallas County permit scraper')
    parser.add_argument('--days', type=int, default=1, help='Number of days to look back')
    parser.add_argument('--sample', action='store_true', help='Use sample data')
    args = parser.parse_args()
    
    exit_code = run_scraper(days=args.days, sample_data=args.sample)
    sys.exit(exit_code)

if __name__ == '__main__':
    main()