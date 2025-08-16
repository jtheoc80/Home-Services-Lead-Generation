#!/bin/bash

# Test script for the secured permits ingest endpoint
# This script tests the authentication and basic functionality

echo "🧪 Testing secured permit ingest endpoint..."
echo "=" | head -c 50

# Test 1: Missing header (should return 401)
echo -e "\n\n🔒 Test 1: Missing X-Ingest-Key header (expect 401)"
echo "curl -X POST -H 'Content-Type: application/json' -d '{\"source\": \"austin\"}' http://localhost:3000/api/permits/ingest"

# Test 2: Invalid header (should return 401)  
echo -e "\n\n🔒 Test 2: Invalid X-Ingest-Key header (expect 401)"
echo "curl -X POST -H 'Content-Type: application/json' -H 'X-Ingest-Key: invalid' -d '{\"source\": \"austin\"}' http://localhost:3000/api/permits/ingest"

# Test 3: Valid header (should work if INGEST_API_KEY is configured)
echo -e "\n\n✅ Test 3: Valid X-Ingest-Key header (expect success if configured properly)"
echo "curl -X POST -H 'Content-Type: application/json' -H 'X-Ingest-Key: \$INGEST_API_KEY' -d '{\"source\": \"austin\"}' http://localhost:3000/api/permits/ingest"

echo -e "\n\n📋 To run these tests:"
echo "1. Set environment variable: export INGEST_API_KEY=your-secret-key"
echo "2. Start your Next.js development server: npm run dev"
echo "3. Run the curl commands above"

echo -e "\n\n🔧 For production deployment:"
echo "1. Add INGEST_API_KEY to your Vercel environment variables"
echo "2. Add INGEST_API_KEY to GitHub repository secrets"
echo "3. Add VERCEL_DOMAIN to GitHub repository secrets (e.g., 'your-app.vercel.app')"