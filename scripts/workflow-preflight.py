#!/usr/bin/env python3
"""
Workflow Preflight Script for Harris County Permit Scraper

Validates required environment variables and performs basic connectivity checks
before running the Harris County permit scraper workflow.

Required Environment Variables:
- SUPABASE_URL: Supabase project URL
- SUPABASE_SERVICE_ROLE_KEY: Supabase service role key for database access
- HC_ISSUED_PERMITS_URL: Harris County permits endpoint URL

This script performs:
1. Environment variable validation
2. Basic URL format validation
3. Supabase connectivity check using REST health probe

Exit codes:
- 0: All checks passed
- 1: Critical validation failure
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


def check_harris_county_endpoint(hc_url):
    """Check Harris County permits endpoint accessibility"""
    if not hc_url:
        log_error("Harris County permits URL not provided")
        return False
    
    try:
        log_info(f"Testing Harris County permits endpoint: {hc_url}")
        
        req = urllib.request.Request(hc_url, method='HEAD')
        start_time = time.time()
        
        with urllib.request.urlopen(req, timeout=15) as response:
            latency = (time.time() - start_time) * 1000
            if response.status == 200:
                log_success(f"Harris County permits endpoint OK ({latency:.0f}ms)")
                return True
            else:
                log_warning(f"Harris County permits endpoint returned status {response.status}")
                return True  # Non-200 might be acceptable for some endpoints
                
    except urllib.error.HTTPError as e:
        log_warning(f"Harris County endpoint HTTP error: {e.code} - {e.reason}")
        # Only accept certain HTTP errors as non-fatal (e.g., 403 Forbidden, 404 Not Found)
        if e.code in (403, 404):
            return True
        else:
            return False
    except urllib.error.URLError as e:
        log_error(f"Harris County endpoint connection error: {e.reason}")
        return False
    except Exception as e:
        log_error(f"Harris County endpoint check failed: {e}")
        return False


def main():
    """Main preflight validation function"""
    log_info("🚀 Starting Harris County permit scraper preflight checks...")
    
    # Check required environment variables
    required_vars = [
        'SUPABASE_URL',
        'SUPABASE_SERVICE_ROLE_KEY', 
        'HC_ISSUED_PERMITS_URL'
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
    
    if missing_vars:
        log_error(f"Missing required environment variables: {', '.join(missing_vars)}")
        log_error("Please refer to docs/workflows-secrets.md for configuration details")
        return 1
    
    # Validate URL formats
    log_info("Validating URL formats...")
    url_checks = [
        (env_vars['SUPABASE_URL'], 'SUPABASE_URL'),
        (env_vars['HC_ISSUED_PERMITS_URL'], 'HC_ISSUED_PERMITS_URL')
    ]
    
    url_valid = True
    for url, name in url_checks:
        if not validate_url_format(url, name):
            url_valid = False
    
    if not url_valid:
        log_error("URL validation failed")
        return 1
    
    # Perform connectivity checks
    log_info("Performing connectivity checks...")
    
    # Check Supabase health
    supabase_ok = check_supabase_health(
        env_vars['SUPABASE_URL'], 
        env_vars['SUPABASE_SERVICE_ROLE_KEY']
    )
    
    # Check Harris County endpoint
    harris_ok = check_harris_county_endpoint(env_vars['HC_ISSUED_PERMITS_URL'])
    
    # Summary
    log_info("Preflight check summary:")
    log_success("✅ Environment variables: All required variables are set")
    log_success("✅ URL formats: All URLs have valid format")
    
    if supabase_ok:
        log_success("✅ Supabase connectivity: Health check and authentication OK")
    else:
        log_error("❌ Supabase connectivity: Health check failed")
    
    if harris_ok:
        log_success("✅ Harris County endpoint: Endpoint is accessible")
    else:
        log_error("❌ Harris County endpoint: Endpoint is not accessible")
    
    if supabase_ok and harris_ok:
        log_success("🎉 All preflight checks passed! Ready to run Harris County permit scraper.")
        log_info("📚 For more information, see: docs/workflows-secrets.md")
        return 0
    else:
        log_error("💥 Preflight checks failed! Please resolve the above issues before running the scraper.")
        log_info("📚 For troubleshooting help, see: docs/workflows-secrets.md")
        return 1


if __name__ == "__main__":
    sys.exit(main())