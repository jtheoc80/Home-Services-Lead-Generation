#!/bin/bash

# Stripe Billing Smoke Test Script
# Tests the complete Stripe integration locally

set -e

echo "🧪 Starting Stripe Billing Smoke Tests"
echo "======================================"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
FRONTEND_PORT=3000
BACKEND_PORT=8000
TIMEOUT=30

# Test results
TESTS_PASSED=0
TESTS_FAILED=0

# Helper functions
log_info() {
    echo -e "${GREEN}✅ $1${NC}"
}

log_warn() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

log_error() {
    echo -e "${RED}❌ $1${NC}"
}

test_passed() {
    TESTS_PASSED=$((TESTS_PASSED + 1))
    log_info "$1"
}

test_failed() {
    TESTS_FAILED=$((TESTS_FAILED + 1))
    log_error "$1"
}

# Check prerequisites
check_prerequisites() {
    echo "🔍 Checking prerequisites..."
    
    # Check if stripe CLI is installed
    if ! command -v stripe &> /dev/null; then
        log_error "Stripe CLI not found. Install from: https://stripe.com/docs/stripe-cli"
        exit 1
    fi
    
    # Check if jq is installed
    if ! command -v jq &> /dev/null; then
        log_warn "jq not found. Installing via package manager recommended for JSON parsing"
    fi
    
    # Check if required files exist
    if [ ! -f "backend/main.py" ]; then
        log_error "Backend main.py not found. Run from project root directory."
        exit 1
    fi
    
    if [ ! -f "frontend/package.json" ]; then
        log_error "Frontend package.json not found. Run from project root directory."
        exit 1
    fi
    
    log_info "Prerequisites check passed"
}

# Check if services are running
check_service() {
    local port=$1
    local name=$2
    
    if curl -s "http://localhost:$port" > /dev/null 2>&1; then
        return 0
    else
        return 1
    fi
}

# Wait for service to be ready
wait_for_service() {
    local port=$1
    local name=$2
    local counter=0
    
    echo "⏳ Waiting for $name to be ready on port $port..."
    
    while [ $counter -lt $TIMEOUT ]; do
        if check_service $port "$name"; then
            log_info "$name is ready"
            return 0
        fi
        sleep 1
        counter=$((counter + 1))
    done
    
    log_error "$name failed to start within $TIMEOUT seconds"
    return 1
}

# Test health endpoints
test_health_endpoints() {
    echo "🏥 Testing health endpoints..."
    
    # Test backend health
    if curl -s "http://localhost:$BACKEND_PORT/healthz" | grep -q '"status":"ok"'; then
        test_passed "Backend health check"
    else
        test_failed "Backend health check"
    fi
    
    # Test backend Stripe status
    local stripe_status=$(curl -s "http://localhost:$BACKEND_PORT/healthz" | jq -r '.stripe' 2>/dev/null || echo "unknown")
    if [ "$stripe_status" = "configured" ]; then
        test_passed "Backend Stripe configuration"
    else
        test_failed "Backend Stripe configuration (status: $stripe_status)"
    fi
    
    # Test frontend health
    if curl -s "http://localhost:$FRONTEND_PORT/api/health" | grep -q '"status":"ok"'; then
        test_passed "Frontend health check"
    else
        test_failed "Frontend health check"
    fi
    
    # Test frontend webhook config
    local webhook_status=$(curl -s "http://localhost:$FRONTEND_PORT/api/health" | jq -r '.webhooksStripe' 2>/dev/null || echo "false")
    if [ "$webhook_status" = "true" ]; then
        test_passed "Frontend webhook configuration"
    else
        test_failed "Frontend webhook configuration"
    fi
}

# Test billing page accessibility
test_billing_page() {
    echo "💳 Testing billing page..."
    
    if curl -s "http://localhost:$FRONTEND_PORT/billing" | grep -q "Choose Your Plan"; then
        test_passed "Billing page loads"
    else
        test_failed "Billing page loads"
    fi
}

# Test API endpoints
test_api_endpoints() {
    echo "🔌 Testing API endpoints..."
    
    # Test billing credit endpoint (may fail without auth)
    local credits_response=$(curl -s -o /dev/null -w "%{http_code}" "http://localhost:$FRONTEND_PORT/api/billing/credits")
    if [ "$credits_response" = "401" ] || [ "$credits_response" = "200" ]; then
        test_passed "Billing credits API endpoint"
    else
        test_failed "Billing credits API endpoint (status: $credits_response)"
    fi
    
    # Test portal endpoint (may fail without auth)
    local portal_response=$(curl -s -o /dev/null -w "%{http_code}" -X POST "http://localhost:$FRONTEND_PORT/api/billing/portal")
    if [ "$portal_response" = "401" ] || [ "$portal_response" = "200" ]; then
        test_passed "Billing portal API endpoint"
    else
        test_failed "Billing portal API endpoint (status: $portal_response)"
    fi
}

# Test webhook endpoint
test_webhook_endpoint() {
    echo "🪝 Testing webhook endpoint..."
    
    # Test webhook endpoint accepts POST
    local webhook_response=$(curl -s -o /dev/null -w "%{http_code}" -X POST "http://localhost:$FRONTEND_PORT/api/webhooks/stripe")
    if [ "$webhook_response" = "400" ]; then
        test_passed "Webhook endpoint accessible (expected 400 for missing signature)"
    else
        test_failed "Webhook endpoint (status: $webhook_response)"
    fi
}

# Test with Stripe CLI (if available and authenticated)
test_stripe_events() {
    echo "⚡ Testing Stripe webhook events..."
    
    # Check if Stripe CLI is authenticated
    if ! stripe config --list | grep -q "test_mode = true"; then
        log_warn "Stripe CLI not authenticated. Skipping webhook event tests."
        log_warn "Run 'stripe login' to enable webhook testing."
        return 0
    fi
    
    # Test webhook forwarding (start in background)
    echo "🔄 Starting webhook forwarding..."
    stripe listen --forward-to "http://localhost:$FRONTEND_PORT/api/webhooks/stripe" > stripe-listen.log 2>&1 &
    STRIPE_PID=$!
    
    # Wait a moment for forwarding to start
    sleep 3
    
    # Trigger a test event
    echo "🎯 Triggering test webhook event..."
    if stripe trigger checkout.session.completed > stripe-trigger.log 2>&1; then
        sleep 2
        
        # Check if webhook was received
        if grep -q "200" stripe-listen.log 2>/dev/null; then
            test_passed "Webhook event processing"
        else
            test_failed "Webhook event processing"
        fi
    else
        test_failed "Stripe event trigger"
    fi
    
    # Clean up
    if [ -n "$STRIPE_PID" ]; then
        kill $STRIPE_PID 2>/dev/null || true
    fi
    rm -f stripe-listen.log stripe-trigger.log
}

# Main execution
main() {
    check_prerequisites
    
    # Check if services are already running
    if ! check_service $BACKEND_PORT "backend"; then
        log_warn "Backend not running on port $BACKEND_PORT"
        log_warn "Start with: cd backend && python main.py"
        exit 1
    fi
    
    if ! check_service $FRONTEND_PORT "frontend"; then
        log_warn "Frontend not running on port $FRONTEND_PORT"
        log_warn "Start with: cd frontend && npm run dev"
        exit 1
    fi
    
    # Wait for services to be ready
    wait_for_service $BACKEND_PORT "backend"
    wait_for_service $FRONTEND_PORT "frontend"
    
    # Run tests
    test_health_endpoints
    test_billing_page
    test_api_endpoints
    test_webhook_endpoint
    test_stripe_events
    
    # Summary
    echo ""
    echo "📊 Test Results Summary"
    echo "======================"
    echo "✅ Tests Passed: $TESTS_PASSED"
    echo "❌ Tests Failed: $TESTS_FAILED"
    echo "🎯 Total Tests: $((TESTS_PASSED + TESTS_FAILED))"
    
    if [ $TESTS_FAILED -eq 0 ]; then
        echo ""
        log_info "🎉 All smoke tests passed! Stripe integration is working correctly."
        exit 0
    else
        echo ""
        log_error "💥 Some tests failed. Check the output above for details."
        exit 1
    fi
}

# Handle script interruption
trap 'echo ""; log_warn "Smoke tests interrupted"; exit 130' INT

# Run main function
main "$@"