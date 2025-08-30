#!/bin/bash
# scripts/generate-frontend-types.sh
# Generate comprehensive TypeScript types for the frontend after swapping permits to leads

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
TYPES_DIR="$PROJECT_ROOT/types"
FRONTEND_TYPES_DIR="$PROJECT_ROOT/frontend/types"

echo "🔧 Generating TypeScript types for frontend (leads-focused)..."

# Create frontend types directory if it doesn't exist
mkdir -p "$FRONTEND_TYPES_DIR"

# Generate enhanced lead types for frontend
cat > "$FRONTEND_TYPES_DIR/leads.ts" << 'EOF'
/**
 * Lead-related TypeScript types for frontend
 * Generated after swapping from permits to leads table
 */

// Base lead interface matching the database schema
export interface Lead {
  id: string;
  created_at: string;
  updated_at?: string;
  source?: string | null;
  name?: string | null;
  phone?: string | null;
  email?: string | null;
  address?: string | null;
  city?: string | null;
  state?: string | null;
  zip?: string | null;
  status?: string | null;
  service?: string | null; // Maps to permit_type in permits context
  county?: string | null;
  metadata?: any; // JSONB field
  // Enhanced fields for dashboard
  lead_score?: number | null;
  score_label?: string | null;
  value?: number | null;
  permit_id?: string | null;
  county_population?: number | null;
  user_id?: string | null;
}

// Lead interface with field mapping for permits-like display
export interface LeadForPermitsView {
  id: string;
  city: string | null; // maps to jurisdiction
  county: string | null;
  service: string | null; // maps to permit_type
  value: number | null;
  status: string | null;
  created_at: string; // maps to issued_date
  address: string | null;
}

// Enhanced lead interface with computed fields for UI
export interface EnhancedLead extends Lead {
  score?: number;
  scoreBreakdown?: {
    recency: number;
    residential: number;
    value: number;
    workClass: number;
  };
  tradeType?: string;
  permitValue?: number;
  lastUpdated?: string;
  permitNumber?: string;
}

// Lead insert payload interface (excludes auto-generated fields)
export interface LeadInsert {
  source?: string | null;
  name?: string | null;
  phone?: string | null;
  email?: string | null;
  address?: string | null;
  city?: string | null;
  state?: string | null;
  zip?: string | null;
  status?: string | null;
  service?: string | null;
  county?: string | null;
  lead_score?: number | null;
  score_label?: string | null;
  value?: number | null;
  permit_id?: string | null;
  county_population?: number | null;
  user_id?: string | null;
  metadata?: any;
}

// Lead update payload interface (all fields optional)
export interface LeadUpdate {
  source?: string | null;
  name?: string | null;
  phone?: string | null;
  email?: string | null;
  address?: string | null;
  city?: string | null;
  state?: string | null;
  zip?: string | null;
  status?: string | null;
  service?: string | null;
  county?: string | null;
  lead_score?: number | null;
  score_label?: string | null;
  value?: number | null;
  permit_id?: string | null;
  county_population?: number | null;
  user_id?: string | null;
  metadata?: any;
}

// API response types
export interface LeadsApiResponse {
  data: Lead[] | null;
  error: string | null;
}

export interface LeadApiResponse {
  data: Lead | null;
  error: string | null;
}

// Form types for lead creation
export interface CreateLeadFormData {
  name: string;
  email: string;
  phone: string;
  source: string;
  address?: string;
  city?: string;
  state?: string;
  zip?: string;
  service?: string;
  county?: string;
}

// Action result types
export interface CreateLeadResult {
  success: boolean;
  error?: string;
  leadId?: string;
}

// Hook return types
export interface UseLeadsReturn {
  leads: Lead[] | null;
  error: string | null;
  loading: boolean;
}

export interface UseEnhancedLeadsReturn {
  leads: EnhancedLead[] | null;
  error: string | null;
  loading: boolean;
}
EOF

# Generate API types
cat > "$FRONTEND_TYPES_DIR/api.ts" << 'EOF'
/**
 * API-related TypeScript types for frontend
 */

// Base API response structure
export interface ApiResponse<T = any> {
  data?: T;
  error?: string;
  message?: string;
  success?: boolean;
}

// Error types
export interface ApiError {
  message: string;
  code?: string;
  status?: number;
}

// Pagination types
export interface PaginationParams {
  page?: number;
  limit?: number;
  orderBy?: string;
  order?: 'asc' | 'desc';
}

export interface PaginatedResponse<T = any> {
  data: T[];
  pagination: {
    page: number;
    limit: number;
    total: number;
    totalPages: number;
    hasNext: boolean;
    hasPrev: boolean;
  };
}

// Filter types for leads
export interface LeadFilters {
  city?: string;
  county?: string;
  status?: string;
  service?: string;
  minValue?: number;
  maxValue?: number;
  startDate?: string;
  endDate?: string;
}
EOF

# Generate utility types
cat > "$FRONTEND_TYPES_DIR/utils.ts" << 'EOF'
/**
 * Utility TypeScript types for frontend
 */

// Common form field types
export interface FormField {
  value: string;
  error?: string;
  touched?: boolean;
}

export interface FormState {
  [key: string]: FormField;
}

// Table/display types
export interface TableColumn {
  key: string;
  label: string;
  sortable?: boolean;
  width?: string;
  align?: 'left' | 'center' | 'right';
}

export interface SortConfig {
  key: string;
  direction: 'asc' | 'desc';
}

// Chart/metrics types
export interface MetricCard {
  title: string;
  value: string | number;
  change?: {
    value: number;
    type: 'increase' | 'decrease';
  };
  color?: 'blue' | 'green' | 'purple' | 'yellow' | 'red';
}

export interface ChartDataPoint {
  x: string | number;
  y: number;
  label?: string;
}

// Navigation types
export interface NavigationItem {
  name: string;
  href: string;
  icon?: string;
  current?: boolean;
}

// Component prop types
export interface BaseComponentProps {
  className?: string;
  children?: React.ReactNode;
}
EOF

# Generate main index file
cat > "$FRONTEND_TYPES_DIR/index.ts" << 'EOF'
/**
 * Main TypeScript types export for frontend
 * Generated after swapping from permits to leads table
 */

// Lead types
export * from './leads';

// API types
export * from './api';

// Utility types
export * from './utils';

// Re-export commonly used types
export type {
  Lead,
  LeadForPermitsView,
  EnhancedLead,
  LeadInsert,
  LeadUpdate,
  CreateLeadFormData,
  CreateLeadResult,
  UseLeadsReturn,
  UseEnhancedLeadsReturn
} from './leads';

export type {
  ApiResponse,
  ApiError,
  PaginatedResponse,
  LeadFilters
} from './api';
EOF

echo "✅ Frontend TypeScript types generated successfully!"
echo "📁 Output directory: $FRONTEND_TYPES_DIR"
echo "📄 Files generated:"
echo "   - leads.ts (Lead-related types with permits mapping)"
echo "   - api.ts (API response and request types)"
echo "   - utils.ts (Utility and component types)"
echo "   - index.ts (Main exports)"
echo ""
echo "💡 Usage in your TypeScript code:"
echo "   import { Lead, LeadForPermitsView, EnhancedLead } from '@/types';"
echo "   import { ApiResponse, LeadFilters } from '@/types';"
echo ""
echo "🔄 Field mappings implemented:"
echo "   - city → jurisdiction (permits context)"
echo "   - service → permit_type (permits context)"
echo "   - created_at → issued_date (permits context)"
echo "   - leads table → permits table (data source swap)"