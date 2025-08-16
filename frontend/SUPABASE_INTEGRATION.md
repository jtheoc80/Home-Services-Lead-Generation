# Frontend Supabase Database Configuration Guide

## Overview

The frontend has been configured to integrate with Supabase database with proper formatting for UI display. This document explains how to set up and use the database integration.

## Configuration Files

### Environment Variables (`.env.local`)

The frontend requires the following environment variables for Supabase integration:

```bash
# Required Supabase Configuration
NEXT_PUBLIC_SUPABASE_URL=https://your-project.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.your_anon_key_here

# Optional Configuration
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
NEXT_PUBLIC_DEFAULT_REGION=tx-houston
LEADS_TEST_MODE=true
```

### Key Components

#### 1. Supabase Client (`lib/supabase-browser.ts`)
- Safe client initialization with null checks
- Proper error handling for missing environment variables
- Helper functions for configuration validation

#### 2. Enhanced Hooks (`hooks/useLeads.ts`)
- `useLeads()` - Basic lead fetching with real-time updates
- `useEnhancedLeads()` - Adds computed fields for UI display (scores, permit values, etc.)
- Proper error handling and loading states

#### 3. Updated Pages
- **Dashboard** (`app/dashboard/page.tsx`) - Shows lead statistics and recent leads
- **Leads** (`app/leads/page.tsx`) - Full lead management interface

## Data Format and UI Display

### Database Schema (from `types/supabase.ts`)
```typescript
interface Lead {
  id: number;
  created_at: string;
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
}
```

### Enhanced Data for UI
The `useEnhancedLeads` hook adds computed fields:
```typescript
interface EnhancedLead extends Lead {
  score?: number;                    // Lead quality score (0-100)
  scoreBreakdown?: {                 // Score components
    recency: number;
    residential: number;
    value: number;
    workClass: number;
  };
  tradeType?: string;                // Formatted service type
  permitValue?: number;              // Estimated permit value
  lastUpdated?: string;              // Relative time ("2 hours ago")
  permitNumber?: string;             // Generated permit number
}
```

## UI Features

### 1. Proper Error Handling
- Shows user-friendly error messages when Supabase is not configured
- Handles network errors gracefully
- Loading states for better UX

### 2. Data Formatting
- **Monetary Values**: Formatted with commas and currency symbols
- **Dates**: Relative time formatting ("2 hours ago", "3 days ago")
- **Addresses**: Fallback to city/state when full address unavailable
- **Status Badges**: Color-coded by lead status (new, qualified, contacted, won)

### 3. Real-time Updates
- Automatic updates when leads change in the database
- WebSocket connection for live data
- Graceful fallback when real-time fails

### 4. Search and Filtering
- County-based filtering with Texas county selector
- Status and trade type filters
- Full-text search across lead data
- Sortable by score, value, or date

## Testing

### Without Database Connection
The app gracefully shows error states and helpful configuration messages.

### With Proper Configuration
1. Replace placeholder values in `.env.local` with your actual Supabase credentials
2. Ensure your Supabase database has the `leads` table with the proper schema
3. The app will automatically connect and display real data

### Test Data
You can add test leads using the "Add Test Lead" button which redirects to `/leads-test` page.

## Integration Benefits

1. **Type Safety**: Full TypeScript integration with database schema
2. **Real-time Updates**: Live data synchronization
3. **Error Handling**: Robust error handling and user feedback
4. **Performance**: Efficient data fetching and caching
5. **User Experience**: Loading states, search, filtering, and proper formatting
6. **Maintainable**: Clean separation of concerns and reusable hooks

## Security

- Uses anonymous key for client-side operations (safe for browser)
- Server-side operations use service role key (in API routes only)
- Proper environment variable handling
- No sensitive data exposed to frontend bundle

## Development Workflow

1. Set up Supabase project and get credentials
2. Update `.env.local` with your credentials
3. Run `npm run dev`
4. Navigate to `/dashboard` or `/leads` to see the integration
5. Use `/leads-test` to add sample data for testing