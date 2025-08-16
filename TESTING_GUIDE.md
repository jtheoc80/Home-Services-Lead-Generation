# Scraping and API Connection Testing Guide

This document provides a comprehensive guide for testing the scraping functionality and API connections to verify that data is being properly pulled and forwarded to Supabase.

## 📋 Overview

The repository includes multiple testing tools to verify:

1. **Scraping Functionality**: Harris County permits scraper
2. **API Connectivity**: External data source connections
3. **Supabase Integration**: Database connectivity and data forwarding
4. **End-to-End Data Flow**: Complete pipeline from scraping to storage

## 🛠️ Available Testing Tools

### 1. Comprehensive Test Suite
```bash
# Full test with real connections
python3 test_scraping_api_connections.py

# Mock mode (safe for CI/testing)
python3 test_scraping_api_connections.py --mock --verbose
```

**Features:**
- ✅ Environment setup validation
- ✅ Supabase connectivity testing
- ✅ Harris County API connection testing
- ✅ Data ingestion pipeline testing
- ✅ Backend API endpoint verification
- ✅ End-to-end data flow validation

### 2. Focused Supabase Testing
```bash
# Environment check only
python3 test_supabase_focused.py --check-env-only

# Full focused test
python3 test_supabase_focused.py
```

**Features:**
- ✅ Environment variable validation
- ✅ Configuration file checks
- ✅ Backend dependency verification
- ✅ Supabase client creation testing
- ✅ Data structure validation

### 3. TypeScript E2E Testing
```bash
# Test Supabase delta (requires tsx)
npm install -g tsx
tsx scripts/e2e_supabase_delta.ts --dry-run
tsx scripts/e2e_supabase_delta.ts --since=3d
```

**Features:**
- ✅ Harris County scraper execution
- ✅ Supabase data insertion verification
- ✅ Before/after record count comparison
- ✅ Delta validation

### 4. Harris County Scraper Testing
```bash
# Direct scraper execution (requires internet)
tsx scripts/harrisCounty/issuedPermits.ts --since 1d
```

**Features:**
- ✅ Live Harris County API connection
- ✅ Data fetching and transformation
- ✅ Supabase insertion
- ✅ Error handling and logging

### 5. Backend API Testing
```bash
# Start backend server
cd backend
uvicorn main:app --host 0.0.0.0 --port 8000

# Test endpoints
curl http://localhost:8000/health/supabase
curl http://localhost:8000/api/supa-env-check
curl -X POST http://localhost:8000/test/lead
```

**Features:**
- ✅ Health check endpoints
- ✅ Environment validation endpoints
- ✅ Test data insertion endpoints
- ✅ API response validation

### 6. Direct Supabase REST API Testing
```bash
# Set environment variables
export SUPABASE_URL="https://your-project.supabase.co"
export SUPABASE_SERVICE_ROLE="your_service_role_key"

# Test REST API directly
curl -X GET "${SUPABASE_URL}/rest/v1/leads" \
  -H "apikey: ${SUPABASE_SERVICE_ROLE}" \
  -H "Authorization: Bearer ${SUPABASE_SERVICE_ROLE}" \
  -H "Content-Type: application/json"
```

Refer to `docs/supabase/SMOKE_TEST.md` for more curl commands.

## 🚀 Quick Start Testing

### Step 1: Environment Setup
```bash
# Copy environment template
cp .env.example .env

# Edit .env with your Supabase credentials
# Required variables:
# - SUPABASE_URL
# - SUPABASE_SERVICE_ROLE_KEY
# - SUPABASE_JWT_SECRET
```

### Step 2: Install Dependencies
```bash
# Python dependencies
cd backend
pip3 install -r requirements.txt
cd ..

# Node.js dependencies
npm install
npm install -g tsx  # For TypeScript execution
```

### Step 3: Run Basic Tests
```bash
# Test environment setup
python3 test_supabase_focused.py --check-env-only

# Test with mock data (safe)
python3 test_scraping_api_connections.py --mock

# Test with real connections (requires credentials)
python3 test_scraping_api_connections.py
```

### Step 4: Advanced Testing
```bash
# Start backend for API testing
cd backend && uvicorn main:app &

# Run E2E test
tsx scripts/e2e_supabase_delta.ts --dry-run

# Run Harris County scraper (requires internet)
tsx scripts/harrisCounty/issuedPermits.ts --since 1d
```

## 📊 Test Results Interpretation

### ✅ Success Indicators
- All environment variables properly configured
- Supabase client connects successfully
- Harris County API responds to requests
- Data flows from scraper to Supabase
- Backend API endpoints respond correctly
- Record counts increase after scraping

### ❌ Common Issues and Solutions

#### Environment Issues
**Problem**: Missing or invalid environment variables
**Solution**:
```bash
# Check current environment
python3 test_supabase_focused.py --check-env-only

# Update .env file with real credentials
# Get from: Supabase Dashboard → Settings → API
```

#### Supabase Connection Issues
**Problem**: Failed to connect to Supabase
**Solutions**:
- Verify URL format: `https://your-project.supabase.co`
- Check service role key (starts with `eyJ`)
- Verify project is not paused in Supabase dashboard
- Check network connectivity

#### Harris County API Issues
**Problem**: Cannot connect to Harris County API
**Solutions**:
- Check internet connectivity
- Verify API endpoint is operational
- Try with different time ranges (`--since 1d`, `--since 7d`)
- Use mock mode for testing: `--mock`

#### Backend API Issues
**Problem**: API endpoints not accessible
**Solutions**:
```bash
# Start backend server
cd backend
uvicorn main:app --host 0.0.0.0 --port 8000

# Check if server is running
curl http://localhost:8000/docs
```

#### Data Flow Issues
**Problem**: Data not appearing in Supabase
**Solutions**:
- Check database table existence
- Verify RLS policies allow service role writes
- Run migrations: check `sql/` directory
- Check logs for specific error messages

## 🔧 Advanced Configuration

### Custom API Endpoints
```bash
# Override default Harris County API
export HC_ISSUED_PERMITS_URL="your_custom_api_url"

# Override backend URL for testing
export BACKEND_URL="http://your-backend:8000"
```

### Test Mode Configuration
```bash
# Enable test mode (bypasses some RLS policies)
export LEADS_TEST_MODE=true

# Configure for specific environments
export ENVIRONMENT=development
export DEBUG=true
```

### Logging Configuration
```bash
# Enable verbose logging
python3 test_scraping_api_connections.py --verbose

# Backend logging
export LOG_LEVEL=DEBUG
cd backend && uvicorn main:app --log-level debug
```

## 📁 Test Files Reference

| File | Purpose | Usage |
|------|---------|-------|
| `test_scraping_api_connections.py` | Comprehensive test suite | Production testing |
| `test_supabase_focused.py` | Focused Supabase testing | Environment validation |
| `scripts/e2e_supabase_delta.ts` | E2E TypeScript tests | Integration testing |
| `scripts/harrisCounty/issuedPermits.ts` | Harris County scraper | Data collection |
| `backend/test_supabase.py` | Backend API test endpoints | API testing |
| `docs/supabase/SMOKE_TEST.md` | Direct REST API tests | Manual testing |
| `demo_testing_infrastructure.py` | Testing demonstration | Learning/documentation |

## 🎯 Testing Checklist

Use this checklist to verify your scraping and API connections:

### Environment Setup
- [ ] `.env` file created with real Supabase credentials
- [ ] Python dependencies installed (`pip3 install -r backend/requirements.txt`)
- [ ] Node.js dependencies installed (`npm install`)
- [ ] TypeScript executor available (`npm install -g tsx`)

### Basic Connectivity
- [ ] Environment variables validate: `python3 test_supabase_focused.py --check-env-only`
- [ ] Backend imports work: `python3 test_supabase_focused.py`
- [ ] Mock tests pass: `python3 test_scraping_api_connections.py --mock`

### Live Connections
- [ ] Supabase connectivity: `python3 test_scraping_api_connections.py`
- [ ] Harris County API access: `tsx scripts/harrisCounty/issuedPermits.ts --since 1d`
- [ ] Backend API endpoints: Start server and test endpoints

### End-to-End Flow
- [ ] E2E test passes: `tsx scripts/e2e_supabase_delta.ts --dry-run`
- [ ] Data appears in Supabase after scraping
- [ ] Record counts increase appropriately
- [ ] No errors in logs

### Verification
- [ ] Direct Supabase queries work (see `docs/supabase/SMOKE_TEST.md`)
- [ ] Backend health endpoints respond
- [ ] Data quality checks pass
- [ ] Performance is acceptable

## 💡 Best Practices

### For Development
- Always test with `--mock` mode first
- Use `--check-env-only` to validate setup
- Start with focused tests before comprehensive ones
- Keep test credentials in `.env`, not in code

### For Production
- Use real credentials for final validation
- Monitor logs during testing
- Test with recent time ranges (`--since 1d`)
- Verify data quality after ingestion

### For CI/CD
- Use mock mode in CI environments
- Test environment validation separately from live connections
- Use appropriate timeouts for network requests
- Cache dependencies to speed up testing

## 🆘 Getting Help

If tests fail:

1. **Run the demonstration**: `python3 demo_testing_infrastructure.py`
2. **Check environment**: `python3 test_supabase_focused.py --check-env-only`
3. **Review logs**: Look for specific error messages
4. **Check documentation**: Review `docs/supabase/SMOKE_TEST.md`
5. **Verify credentials**: Ensure Supabase project is active and keys are correct

For additional help, check the repository's README.md or create an issue with:
- Test output/logs
- Environment configuration (without sensitive data)
- Expected vs actual behavior