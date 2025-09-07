# City of Houston (COH) Adapters

TypeScript adapters for extracting permit data from City of Houston sources.

## Files Created

- `scripts/adapters/houstonXlsx.ts` - XLSX file parser for Houston permits
- `scripts/adapters/houstonSoldPermits.ts` - HTML scraper for sold permits
- `scripts/lib/supabaseUpsert.ts` - Supabase upsert utility  
- `scripts/etlHouston.ts` - Main ETL runner

## Usage

Run the Houston ETL process:

```bash
npm run etl:houston
```

## Environment Variables Required

```bash
HOUSTON_WEEKLY_XLSX_URL="https://example.com/houston-weekly-permits.xlsx"
HOUSTON_SOLD_PERMITS_URL="https://example.com/houston-sold-permits"
SUPABASE_URL="https://your-project.supabase.co" 
SUPABASE_SERVICE_ROLE_KEY="your-service-role-key"
DAYS=7  # Optional, defaults to 7 days lookback
```

## Data Format

The adapters produce standardized permit records:

```typescript
type Permit = {
  source_system: "city_of_houston";
  permit_id: string;
  issue_date: string;  // ISO date string
  trade: string;       // "Electrical" | "Plumbing" | "Mechanical" | "General"
  address?: string;
  zipcode?: string;
  valuation?: number | null;
  contractor?: string | null;
  raw?: any;           // Original source data
};
```

## Features

- **Flexible field mapping** - Handles various column names automatically
- **Date filtering** - Only processes permits from specified time window  
- **Trade normalization** - Maps work types to standard categories
- **Deduplication** - Removes duplicates across data sources
- **Robust error handling** - Graceful handling of malformed data
- **Logging and monitoring** - Detailed ETL summaries for CI/CD

## Testing

Test the adapters without external dependencies:

```bash
npx tsx scripts/test-coh-adapters.ts
npx tsx scripts/test-xlsx-parsing.ts  
npx tsx scripts/test-html-parsing.ts
```