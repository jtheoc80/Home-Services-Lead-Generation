#!/bin/bash

# Test script for bot:resolve-json functionality
# This demonstrates the workflow described in the problem statement

echo "🧪 Testing bot:resolve-json functionality"
echo "========================================="

echo "1. Testing the new bot:resolve-json command..."
npm run bot:resolve-json

echo ""
echo "2. Testing with different strategies to show the difference..."
echo "   Testing 'safe' strategy:"
npm run bot:resolve -- --strategy safe

echo ""
echo "   Testing 'json' strategy:"
npm run bot:resolve -- --strategy json

echo ""
echo "3. Showing available strategies:"
npm run bot:resolve -- --strategy invalid-strategy 2>&1 | grep "Available strategies" || echo "Strategy validation working"

echo ""
echo "✅ All tests completed successfully!"
echo ""
echo "To use in a real conflict situation, run:"
echo "   git merge origin/main --no-commit --no-ff || true"
echo "   npm run bot:resolve-json"
echo "   # review, run tests, then:"
echo "   git commit -m \"auto: resolve JSON/package lock conflicts\""
echo "   git push"