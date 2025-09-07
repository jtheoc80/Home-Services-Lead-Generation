#!/usr/bin/env python3
"""
Houston Preflight Script for City of Houston ETL Workflow

Validates required environment variables and performs basic connectivity checks
before running the City of Houston permit scraper workflow.

Required Environment Variables:
- SUPABASE_URL: Supabase project URL
- SUPABASE_SERVICE_ROLE_KEY: Supabase service role key for database access
- HOUSTON_WEEKLY_XLSX_URL: Houston weekly permits XLSX file URL

Optional Environment Variables:
- HOUSTON_SOLD_PERMITS_URL: Houston sold permits data URL

This script performs:
1. Environment variable validation
2. Basic URL format validation
3. Supabase connectivity check using REST health probe
4. Houston endpoints connectivity check (non-blocking)

Exit codes:
- 0: All critical checks passed (Houston endpoints may be unreachable)
- 1: Critical validation failure (missing env vars, invalid URLs, Supabase issues)
"""

import os
import sys
import urllib.parse
import urllib.request
import json
import time


def log_info(message):
    """Log info message with timestamp"""
    print(f"ℹ️  {message}")


def log_success(message):
    """Log success message with timestamp"""
    print(f"✅ {message}")


def log_warning(message):
    """Log warning message with timestamp"""
    print(f"⚠️  {message}")


def log_error(message):
    """Log error message with timestamp"""
    print(f"❌ {message}")


def validate_url_format(url, name):
    """Validate URL format and scheme"""
    if not url:
        log_error(f"{name} is empty or not set")
        return False
    
    try:
        parsed = urllib.parse.urlparse(url)
        if not parsed.scheme or not parsed.netloc:
            log_error(f"{name} is not a valid URL: {url}")
            return False
        
        if parsed.scheme not in ['http', 'https']:
            log_error(f"{name} must use http or https scheme: {url}")
            return False
            
        log_success(f"{name} format is valid")
        return True
    except Exception as e:
        log_error(f"{name} validation failed: {e}")
        return False


def check_supabase_health(supabase_url, service_role_key):
    """Check Supabase health using REST endpoint"""
    if not supabase_url or not service_role_key:
        log_error("Supabase URL or service role key not provided")
        return False
    
    try:
        # Test 1: Health endpoint check
        health_url = f"{supabase_url.rstrip('/')}/auth/v1/health"
        log_info(f"Testing Supabase health endpoint: {health_url}")
        
        req = urllib.request.Request(health_url, method='HEAD')
        start_time = time.time()
        
        with urllib.request.urlopen(req, timeout=10) as response:
            health_latency = (time.time() - start_time) * 1000
            if response.status == 200:
                log_success(f"Supabase health endpoint OK ({health_latency:.0f}ms)")
            else:
                log_error(f"Supabase health endpoint returned status {response.status}")
                return False
        
        # Test 2: Service role authentication test
        query_url = f"{supabase_url.rstrip('/')}/rest/v1/pg_catalog.pg_tables?select=schemaname,tablename&limit=1"
        log_info("Testing Supabase service role authentication...")
        
        req = urllib.request.Request(query_url)
        req.add_header('Authorization', f'Bearer {service_role_key}')
        req.add_header('apikey', service_role_key)
        req.add_header('Accept', 'application/json')
        
        start_time = time.time()
        with urllib.request.urlopen(req, timeout=10) as response:
            query_latency = (time.time() - start_time) * 1000
            if response.status == 200:
                log_success(f"Supabase service role authentication OK ({query_latency:.0f}ms)")
                return True
            else:
                log_error(f"Supabase service role query failed with status {response.status}")
                return False
                
    except urllib.error.HTTPError as e:
        log_error(f"Supabase HTTP error: {e.code} - {e.reason}")
        return False
    except urllib.error.URLError as e:
        log_error(f"Supabase connection error: {e.reason}")
        return False
    except Exception as e:
        log_error(f"Supabase check failed: {e}")
        return False


def check_houston_endpoint(url, name, critical=False):
    """Check Houston endpoint accessibility (non-blocking by default)
    
    Returns:
        tuple: (process_success, actually_reachable)
        - process_success: Whether the check should fail the overall process
        - actually_reachable: Whether the endpoint is actually reachable
    """
    if not url:
        if critical:
            log_error(f"{name} URL not provided")
            return False, False
        else:
            log_warning(f"{name} URL not provided - skipping check")
            return True, False
    
    try:
        log_info(f"Testing {name}: {url}")
        
        req = urllib.request.Request(url, method='HEAD')
        start_time = time.time()
        
        with urllib.request.urlopen(req, timeout=15) as response:
            latency = (time.time() - start_time) * 1000
            if response.status in [200, 301, 302]:
                log_success(f"{name} OK ({latency:.0f}ms)" if response.status == 200 else f"{name} redirected (status {response.status})")
                return True, True
            else:
                log_warning(f"{name} returned status {response.status}")
                return not critical, False
                
    except urllib.error.HTTPError as e:
        log_warning(f"{name} HTTP error: {e.code} - {e.reason}")
        # Accept certain HTTP errors as non-fatal (e.g., 403 Forbidden, 404 Not Found)
        if e.code == 403:
            log_info(f"HTTP 403 is acceptable for {name}")
            return True, True  # Blocked but reachable
        elif e.code == 404:
            log_info(f"HTTP 404 is acceptable for {name}")
            return True, False  # Not found, not actually reachable
        else:
            if critical:
                log_error(f"{name} failed with HTTP {e.code}")
                return False, False
            else:
                log_warning(f"{name} failed with HTTP {e.code} (non-critical)")
                return True, False
    except urllib.error.URLError as e:
        if critical:
            log_error(f"{name} connection error: {e.reason}")
            return False, False
        else:
            log_warning(f"{name} connection error: {e.reason} (non-critical)")
            log_info("💡 If this is a network access issue, consider:")
            log_info("   - Adding www.houstontx.gov to allowlist")
            log_info("   - Using a self-hosted runner with network access")
            return True, False
    except Exception as e:
        if critical:
            log_error(f"{name} check failed: {e}")
            return False, False
        else:
            log_warning(f"{name} check failed: {e} (non-critical)")
            return True, False


def main():
    """Main preflight validation function"""
    log_info("🚀 Starting City of Houston ETL preflight checks...")
    
    # Check required environment variables
    required_vars = [
        'SUPABASE_URL',
        'SUPABASE_SERVICE_ROLE_KEY', 
        'HOUSTON_WEEKLY_XLSX_URL'
    ]
    
    optional_vars = [
        'HOUSTON_SOLD_PERMITS_URL'
    ]
    
    missing_vars = []
    env_vars = {}
    
    log_info("Checking required environment variables...")
    for var in required_vars:
        value = os.environ.get(var)
        if not value:
            missing_vars.append(var)
            log_error(f"Environment variable {var} is not set")
        else:
            env_vars[var] = value
            log_success(f"Environment variable {var} is set")
    
    log_info("Checking optional environment variables...")
    for var in optional_vars:
        value = os.environ.get(var)
        if value:
            env_vars[var] = value
            log_success(f"Environment variable {var} is set")
        else:
            log_info(f"Environment variable {var} is not set (optional)")
    
    if missing_vars:
        log_error(f"Missing required environment variables: {', '.join(missing_vars)}")
        log_error("Please refer to docs/coh-etl-script.md for configuration details")
        return 1
    
    # Validate URL formats
    log_info("Validating URL formats...")
    url_checks = [
        (env_vars['SUPABASE_URL'], 'SUPABASE_URL'),
        (env_vars['HOUSTON_WEEKLY_XLSX_URL'], 'HOUSTON_WEEKLY_XLSX_URL')
    ]
    
    if 'HOUSTON_SOLD_PERMITS_URL' in env_vars:
        url_checks.append((env_vars['HOUSTON_SOLD_PERMITS_URL'], 'HOUSTON_SOLD_PERMITS_URL'))
    
    url_valid = True
    for url, name in url_checks:
        if not validate_url_format(url, name):
            url_valid = False
    
    if not url_valid:
        log_error("URL validation failed")
        return 1
    
    # Perform connectivity checks
    log_info("Performing connectivity checks...")
    
    # Check Supabase health (critical)
    supabase_ok = check_supabase_health(
        env_vars['SUPABASE_URL'], 
        env_vars['SUPABASE_SERVICE_ROLE_KEY']
    )
    
    # Check Houston endpoints (non-critical)
    log_info("Checking Houston endpoints (non-critical)...")
    houston_weekly_process_ok, houston_weekly_reachable = check_houston_endpoint(
        env_vars['HOUSTON_WEEKLY_XLSX_URL'], 
        "Houston Weekly XLSX endpoint", 
        critical=False
    )
    
    houston_sold_process_ok = True
    houston_sold_reachable = True
    if 'HOUSTON_SOLD_PERMITS_URL' in env_vars:
        houston_sold_process_ok, houston_sold_reachable = check_houston_endpoint(
            env_vars['HOUSTON_SOLD_PERMITS_URL'], 
            "Houston Sold Permits endpoint", 
            critical=False
        )
    
    # Check Houston city website (non-critical, informational)
    houston_website_process_ok, houston_website_reachable = check_houston_endpoint(
        "https://www.houstontx.gov/planning/DevelopRegs/dev_reports.html",
        "Houston City Planning website",
        critical=False
    )
    
    # Summary
    log_info("Preflight check summary:")
    log_success("Environment variables: All required variables are set")
    log_success("URL formats: All URLs have valid format")
    
    if supabase_ok:
        log_success("Supabase connectivity: Health check and authentication OK")
    else:
        log_error("Supabase connectivity: Health check failed")
    
    # Houston endpoints are non-critical
    all_houston_reachable = houston_weekly_reachable and houston_sold_reachable and houston_website_reachable
    if all_houston_reachable:
        log_success("Houston endpoints: All endpoints are accessible")
    else:
        log_warning("Houston endpoints: Some endpoints may be unreachable")
        log_info("   This is not critical - the ETL may still work with cached/alternative data")
    
    # Only fail on critical issues (Supabase)
    if supabase_ok:
        log_success("🎉 Critical preflight checks passed! Ready to run City of Houston ETL.")
        log_info("📚 For more information, see: docs/coh-etl-script.md")
        if not all_houston_reachable:
            log_warning("⚠️  Note: Some Houston endpoints are unreachable but ETL will proceed")
            log_info("💡 If connectivity issues persist, consider allowlisting www.houstontx.gov")
        return 0
    else:
        log_error("💥 Critical preflight checks failed! Cannot proceed with ETL.")
        log_info("📚 For troubleshooting help, see: docs/coh-etl-script.md")
        return 1


if __name__ == "__main__":
    sys.exit(main())