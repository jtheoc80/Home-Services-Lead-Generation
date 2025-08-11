#!/bin/bash
"""
Local Stripe webhook development script.

This script sets up local webhook forwarding using the Stripe CLI.
It runs the backend server and forwards webhook events from Stripe
to the local development environment.

Prerequisites:
- Stripe CLI installed (https://stripe.com/docs/stripe-cli)
- Backend server dependencies installed
- Environment variables configured

Usage:
    ./scripts/stripe_webhook_local.sh
"""

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🏠 LeadLedgerPro - Local Stripe Webhook Development${NC}"
echo "================================================"

# Check if Stripe CLI is installed
if ! command -v stripe &> /dev/null; then
    echo -e "${RED}❌ Stripe CLI not found${NC}"
    echo "Please install the Stripe CLI:"
    echo "  https://stripe.com/docs/stripe-cli#install"
    echo ""
    echo "macOS: brew install stripe/stripe-cli/stripe"
    echo "Linux: wget -qO- https://github.com/stripe/stripe-cli/releases/download/v1.19.4/stripe_1.19.4_linux_x86_64.tar.gz | tar -xz && sudo mv stripe /usr/local/bin/"
    exit 1
fi

echo -e "${GREEN}✅ Stripe CLI found${NC}"

# Check if backend environment is set up
if [ ! -f "backend/.env" ]; then
    echo -e "${YELLOW}⚠️  Backend .env file not found${NC}"
    echo "Creating .env from .env.example..."
    if [ -f "backend/.env.example" ]; then
        cp backend/.env.example backend/.env
        echo -e "${YELLOW}Please edit backend/.env and configure your Stripe keys${NC}"
    else
        echo -e "${RED}❌ backend/.env.example not found${NC}"
        exit 1
    fi
fi

# Check for Stripe secret key
if ! grep -q "STRIPE_SECRET_KEY=sk_" backend/.env 2>/dev/null; then
    echo -e "${YELLOW}⚠️  STRIPE_SECRET_KEY not configured in backend/.env${NC}"
    echo "Please set your Stripe secret key in backend/.env"
    echo "Get your test keys from: https://dashboard.stripe.com/test/apikeys"
fi

# Function to cleanup background processes
cleanup() {
    echo -e "\n${YELLOW}🧹 Cleaning up...${NC}"
    if [ ! -z "$BACKEND_PID" ]; then
        kill $BACKEND_PID 2>/dev/null || true
        echo "Stopped backend server"
    fi
    if [ ! -z "$STRIPE_PID" ]; then
        kill $STRIPE_PID 2>/dev/null || true
        echo "Stopped Stripe webhook forwarding"
    fi
    exit 0
}

# Set up signal handlers
trap cleanup SIGINT SIGTERM

# Change to project directory
cd "$(dirname "$0")/.."

# Install backend dependencies if needed
if [ ! -d "backend/.venv" ] && [ ! -f "backend/.deps-installed" ]; then
    echo -e "${BLUE}📦 Installing backend dependencies...${NC}"
    cd backend
    pip install -r requirements.txt
    touch .deps-installed
    cd ..
fi

# Start backend server in background
echo -e "${BLUE}🚀 Starting backend server...${NC}"
cd backend
python main.py &
BACKEND_PID=$!
cd ..

# Wait a moment for server to start
sleep 3

# Check if backend is running
if ! curl -s http://localhost:8000/healthz > /dev/null; then
    echo -e "${RED}❌ Backend server failed to start${NC}"
    echo "Check backend logs for errors"
    kill $BACKEND_PID 2>/dev/null || true
    exit 1
fi

echo -e "${GREEN}✅ Backend server running on http://localhost:8000${NC}"

# Login to Stripe CLI (if not already logged in)
if ! stripe config --list | grep -q "test_mode_api_key"; then
    echo -e "${BLUE}🔐 Logging in to Stripe CLI...${NC}"
    stripe login
fi

# Start webhook forwarding
echo -e "${BLUE}📡 Starting webhook forwarding...${NC}"
echo "Forwarding Stripe webhooks to http://localhost:8000/webhooks/stripe"
echo ""
echo -e "${GREEN}Webhook endpoint secret will be displayed below.${NC}"
echo -e "${YELLOW}Copy the webhook secret (whsec_...) to your backend/.env file as STRIPE_WEBHOOK_SECRET${NC}"
echo ""

stripe listen --forward-to localhost:8000/webhooks/stripe &
STRIPE_PID=$!

# Give some time for webhook forwarding to establish
sleep 2

echo ""
echo -e "${GREEN}🎉 Local webhook development environment ready!${NC}"
echo ""
echo "Available endpoints:"
echo "  🌐 Backend API: http://localhost:8000"
echo "  📋 API Docs: http://localhost:8000/docs"
echo "  ❤️  Health Check: http://localhost:8000/healthz"
echo ""
echo "Test webhook events:"
echo "  stripe trigger checkout.session.completed"
echo "  stripe trigger invoice.paid"
echo "  stripe trigger customer.subscription.updated"
echo ""
echo -e "${YELLOW}Press Ctrl+C to stop all services${NC}"

# Wait for processes
wait $BACKEND_PID $STRIPE_PID