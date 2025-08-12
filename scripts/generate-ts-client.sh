#!/bin/bash
# scripts/generate-ts-client.sh
# Auto-generate TypeScript client from OpenAPI spec

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
OPENAPI_FILE="$PROJECT_ROOT/openapi.yaml"
OUTPUT_DIR="$PROJECT_ROOT/frontend/lib/api"

echo "🔧 Generating TypeScript API client..."

# Check if OpenAPI file exists
if [ ! -f "$OPENAPI_FILE" ]; then
    echo "❌ Error: openapi.yaml not found at $OPENAPI_FILE"
    exit 1
fi

# Install openapi-typescript if not already installed
if ! command -v openapi-typescript &> /dev/null; then
    echo "📦 Installing openapi-typescript..."
    npm install -g openapi-typescript
fi

# Create output directory if it doesn't exist
mkdir -p "$OUTPUT_DIR"

# Generate TypeScript types
echo "📝 Generating TypeScript types..."
openapi-typescript "$OPENAPI_FILE" -o "$OUTPUT_DIR/types.ts"

# Generate runtime client (using openapi-typescript-fetch)
echo "📝 Generating TypeScript client..."
cat > "$OUTPUT_DIR/client.ts" << 'EOF'
/* tslint:disable */
/* eslint-disable */
/**
 * Auto-generated API client
 * Generated from openapi.yaml - do not edit manually
 */

import { paths } from './types';
import { Fetcher } from 'openapi-typescript-fetch';

// Create the fetcher instance
const fetcher = Fetcher.for<paths>();

// Configure base URL and default options
fetcher.configure({
  baseUrl: process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000',
  init: {
    headers: {
      'Content-Type': 'application/json',
    },
  },
});

// Export typed API methods
export const api = {
  // Health endpoints
  getHealth: fetcher.path('/health').method('get').create(),
  
  // Admin endpoints
  getAdminStatus: fetcher.path('/admin/status').method('get').create(),
  
  // Export endpoints
  exportData: fetcher.path('/export').method('post').create(),
  
  // Subscription endpoints
  getSubscription: fetcher.path('/subscription').method('get').create(),
  cancelSubscription: fetcher.path('/subscription/cancel').method('post').create(),
  reactivateSubscription: fetcher.path('/subscription/reactivate').method('post').create(),
};

export default api;
EOF

# Update the main API index file
cat > "$OUTPUT_DIR/index.ts" << 'EOF'
/* tslint:disable */
/* eslint-disable */
/**
 * Auto-generated API exports
 * Generated from openapi.yaml - do not edit manually
 */

export * from './types';
export * from './client';
export { default as api } from './client';
EOF

echo "✅ TypeScript API client generated successfully!"
echo "📁 Output directory: $OUTPUT_DIR"
echo "📄 Files generated:"
echo "   - types.ts (TypeScript type definitions)"
echo "   - client.ts (API client with typed methods)"
echo "   - index.ts (Main exports)"
echo ""
echo "💡 Usage in your TypeScript code:"
echo "   import { api } from '@/lib/api';"
echo "   const health = await api.getHealth();"