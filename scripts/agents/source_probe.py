#!/usr/bin/env python3
"""
Source health probe script for self-hosted GitHub Actions runners.

This script checks the health of various data sources used by the 
Home Services Lead Generation platform. It's designed to run on 
self-hosted runners with internet connectivity.
"""

import sys
import requests
import yaml
import json
import time
from datetime import datetime, timezone
from typing import Dict, List, Any


def load_sources_config() -> Dict[str, Any]:
    """Load sources configuration from config files."""
    sources = {}
    
    # Try to load various source configs
    config_files = [
        'permit_leads/config/sources.yaml',
        'config/sources.yaml',
        'config/sources_tx.yaml'
    ]
    
    for config_file in config_files:
        try:
            with open(config_file, 'r') as f:
                config = yaml.safe_load(f)
                if config and 'sources' in config:
                    # Handle list format (like sources_tx.yaml)
                    sources_list = config['sources']
                    if isinstance(sources_list, list):
                        for source in sources_list:
                            if isinstance(source, dict) and 'id' in source:
                                source_id = source['id']
                                # Create a proper URL for health checking
                                if source.get('kind') == 'socrata' and source.get('domain'):
                                    domain = source['domain']
                                    # Check if domain already includes a protocol
                                    if domain.startswith('http://') or domain.startswith('https://'):
                                        url = domain
                                    else:
                                        protocol = source.get('protocol', 'https')
                                        url = f"{protocol}://{domain}"
                                else:
                                    url = source.get('url') or source.get('endpoint')
                                
                                sources[source_id] = {
                                    'name': source.get('name', source_id),
                                    'url': url,
                                    'kind': source.get('kind', 'unknown')
                                }
                    # Handle dict format (traditional)
                    elif isinstance(sources_list, dict):
                        sources.update(sources_list)
                    
                    print(f"✅ Loaded {len(sources)} sources from {config_file}")
        except FileNotFoundError:
            print(f"⚠️  Config file not found: {config_file}")
        except Exception as e:
            print(f"❌ Error loading {config_file}: {e}")
    
    return sources


def probe_http_source(url: str, timeout: int = 30) -> Dict[str, Any]:
    """Probe an HTTP source and return health metrics."""
    start_time = time.time()
    
    try:
        headers = {
            'User-Agent': 'LeadLedgerHealthProbe/1.0 (+github-actions-selfhosted)'
        }
        
        response = requests.get(url, timeout=timeout, headers=headers)
        response_time = int((time.time() - start_time) * 1000)
        
        return {
            'status': 'online' if response.status_code == 200 else 'limited',
            'status_code': response.status_code,
            'response_time_ms': response_time,
            'content_length': len(response.content) if response.content else 0,
            'error_message': None if response.status_code == 200 else f"HTTP {response.status_code}"
        }
        
    except requests.exceptions.Timeout:
        return {
            'status': 'offline',
            'status_code': None,
            'response_time_ms': timeout * 1000,
            'content_length': 0,
            'error_message': f'Timeout after {timeout}s'
        }
    except requests.exceptions.ConnectionError as e:
        return {
            'status': 'offline',
            'status_code': None,
            'response_time_ms': int((time.time() - start_time) * 1000),
            'content_length': 0,
            'error_message': f'Connection error: {str(e)[:100]}'
        }
    except Exception as e:
        return {
            'status': 'offline',
            'status_code': None,
            'response_time_ms': int((time.time() - start_time) * 1000),
            'content_length': 0,
            'error_message': f'Error: {str(e)[:100]}'
        }


def probe_sources() -> List[Dict[str, Any]]:
    """Probe all configured sources and return health results."""
    sources = load_sources_config()
    results = []
    
    # Default sources if config is empty
    if not sources:
        default_sources = {
            'houston_weekly': {
                'name': 'Houston Weekly Reports',
                'url': 'https://www.houstontx.gov/planning/DevelopRegs/dev_reports.html'
            },
            'harris_county': {
                'name': 'Harris County Permits',
                'url': 'https://data.harriscountytx.gov'
            },
            'dallas_permits': {
                'name': 'Dallas County Permits',
                'url': 'https://www.dallascounty.org'
            }
        }
        sources = default_sources
        print("ℹ️  Using default sources (no config found)")
    
    for source_id, source_config in sources.items():
        print(f"🔍 Probing {source_id}...")
        
        # Extract URL from various possible config formats
        url = None
        if isinstance(source_config, dict):
            url = source_config.get('url') or source_config.get('endpoint') or source_config.get('base_url')
        elif isinstance(source_config, str):
            url = source_config
            
        if not url:
            print(f"⚠️  No URL found for {source_id}")
            continue
            
        probe_result = probe_http_source(url)
        
        result = {
            'source_key': source_id,
            'source_name': source_config.get('name', source_id) if isinstance(source_config, dict) else source_id,
            'source_url': url,
            'last_check': datetime.now(timezone.utc).isoformat(),
            **probe_result
        }
        
        results.append(result)
        
        # Print result
        status_emoji = {'online': '✅', 'limited': '⚠️', 'offline': '❌'}.get(result['status'], '❓')
        print(f"  {status_emoji} {result['status']} ({result['response_time_ms']}ms)")
        if result['error_message']:
            print(f"     Error: {result['error_message']}")
    
    return results


def main():
    """Main entry point."""
    print("🚀 Starting source health probe...")
    print(f"📅 Timestamp: {datetime.now(timezone.utc).isoformat()}")
    print()
    
    try:
        results = probe_sources()
        
        # Summary
        print()
        print("📊 Summary:")
        total = len(results)
        online = len([r for r in results if r['status'] == 'online'])
        limited = len([r for r in results if r['status'] == 'limited'])
        offline = len([r for r in results if r['status'] == 'offline'])
        
        print(f"   Total sources: {total}")
        print(f"   ✅ Online: {online}")
        print(f"   ⚠️  Limited: {limited}")
        print(f"   ❌ Offline: {offline}")
        
        # Output JSON for consumption by other tools
        output_file = 'artifacts/source_health.json'
        try:
            with open(output_file, 'w') as f:
                json.dump({
                    'timestamp': datetime.now(timezone.utc).isoformat(),
                    'summary': {
                        'total': total,
                        'online': online,
                        'limited': limited,
                        'offline': offline
                    },
                    'sources': results
                }, f, indent=2)
            print(f"📄 Results saved to {output_file}")
        except Exception as e:
            print(f"⚠️  Could not save results: {e}")
        
        # Exit with error code if any sources are offline
        if offline > 0:
            print(f"\n❌ {offline} sources are offline")
            sys.exit(1)
        elif limited > 0:
            print(f"\n⚠️  {limited} sources have limited availability")
            sys.exit(0)
        else:
            print("\n✅ All sources are online")
            sys.exit(0)
            
    except Exception as e:
        print(f"💥 Fatal error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()