#!/bin/bash

# Debug API Endpoint Test Script
# This script demonstrates how to use the secure debug endpoint

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🔐 Debug API Endpoint Test Script${NC}"
echo "=================================="
echo

# Configuration
BASE_URL="${BASE_URL:-http://localhost:3000}"
TRACE_ID="${TRACE_ID:-test-trace-id}"
DEBUG_KEY="${DEBUG_API_KEY:-4fee8941cb95a2d8428538975c181a0adba64dfd15b99c97480b3c653d5855eb}"

echo -e "${YELLOW}Configuration:${NC}"
echo "Base URL: $BASE_URL"
echo "Trace ID: $TRACE_ID"
echo "Debug Key: [REDACTED]"
echo

# Function to make curl request and show results
test_request() {
    local description="$1"
    local headers="$2"
    local expected_status="$3"
    
    echo -e "${BLUE}Testing: $description${NC}"
    echo "Command: curl -s -w '%{http_code}' -X GET '$BASE_URL/api/leads/trace/$TRACE_ID' $headers"
    
    if [ -n "$headers" ]; then
        response=$(curl -s -w "%{http_code}" -X GET "$BASE_URL/api/leads/trace/$TRACE_ID" $headers)
    else
        response=$(curl -s -w "%{http_code}" -X GET "$BASE_URL/api/leads/trace/$TRACE_ID")
    fi
    
    # Extract status code (last 3 characters)
    status_code="${response: -3}"
    # Extract response body (everything except last 3 characters)
    body="${response%???}"
    
    echo "Status: $status_code"
    if [ -n "$body" ]; then
        echo "Response: $body" | jq . 2>/dev/null || echo "Response: $body"
    fi
    
    if [ "$status_code" = "$expected_status" ]; then
        echo -e "${GREEN}✅ PASS${NC}"
    else
        echo -e "${RED}❌ FAIL (expected $expected_status)${NC}"
    fi
    echo
}

echo -e "${YELLOW}Running test cases...${NC}"
echo

# Test 1: No authentication header (should return 401)
test_request "No X-Debug-Key header" "" "401"

# Test 2: Wrong authentication key (should return 401)
test_request "Wrong X-Debug-Key" "-H 'X-Debug-Key: wrong-key'" "401"

# Test 3: Empty authentication key (should return 401)
test_request "Empty X-Debug-Key" "-H 'X-Debug-Key: '" "401"

# Test 4: Correct authentication key (should work - 200, 400, or 500 depending on data)
test_request "Correct X-Debug-Key" "-H 'X-Debug-Key: $DEBUG_KEY'" "401|200|400|500"

echo -e "${YELLOW}Example usage commands:${NC}"
echo

echo -e "${GREEN}1. Basic request with authentication:${NC}"
echo "curl -X GET \\"
echo "  '$BASE_URL/api/leads/trace/your-trace-id' \\"
echo "  -H 'X-Debug-Key: $DEBUG_KEY'"
echo

echo -e "${GREEN}2. Pretty JSON output:${NC}"
echo "curl -X GET \\"
echo "  '$BASE_URL/api/leads/trace/your-trace-id' \\"
echo "  -H 'X-Debug-Key: $DEBUG_KEY' \\"
echo "  -H 'Accept: application/json' | jq ."
echo

echo -e "${GREEN}3. Testing unauthorized access (returns 401):${NC}"
echo "curl -X GET '$BASE_URL/api/leads/trace/test-id'"
echo

echo -e "${GREEN}4. Testing with wrong key (returns 401):${NC}"
echo "curl -X GET \\"
echo "  '$BASE_URL/api/leads/trace/test-id' \\"
echo "  -H 'X-Debug-Key: wrong-key'"
echo

echo -e "${YELLOW}Environment setup:${NC}"
echo

echo -e "${GREEN}Generate a new debug key:${NC}"
echo "node -e \"console.log(require('crypto').randomBytes(32).toString('hex'))\""
echo

echo -e "${GREEN}Set environment variable:${NC}"
echo "export DEBUG_API_KEY=\"your-64-char-hex-key\""
echo

echo -e "${GREEN}Add to .env file:${NC}"
echo "echo \"DEBUG_API_KEY=your-64-char-hex-key\" >> .env"
echo

echo -e "${GREEN}For Vercel deployment:${NC}"
echo "1. Go to Vercel Dashboard → Project → Settings → Environment Variables"
echo "2. Add DEBUG_API_KEY with your generated key"
echo "3. Redeploy your application"
echo

echo -e "${GREEN}For GitHub Secrets:${NC}"
echo "1. Go to GitHub Repository → Settings → Secrets and variables → Actions"
echo "2. Add repository secret: DEBUG_API_KEY"
echo "3. Use in GitHub Actions: \${{ secrets.DEBUG_API_KEY }}"
echo

echo -e "${BLUE}🔐 Debug endpoint security test completed!${NC}"