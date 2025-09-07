# Houston Weekly XLSX Adapter

This is a tiny Houston weekly XLSX adapter implementation for bulk permit processing.

## Files Created

- `scripts/houstonWeekly.ts` - Main adapter implementation
- `scripts/supabaseSink.ts` - Type definitions for Permit interface
- `scripts/test_houstonWeekly.ts` - Basic functionality test
- `scripts/test_houstonWeekly_core.ts` - Core logic validation test
- `scripts/test_houstonWeekly_integration.ts` - Integration test with existing ecosystem

## Usage

```typescript
import { fetchHoustonWeekly } from "./scripts/houstonWeekly";

// Fetch permits from the last 7 days (default)
const permits = await fetchHoustonWeekly(xlsxUrl);

// Fetch permits from the last 14 days
const permits = await fetchHoustonWeekly(xlsxUrl, 14);
```

## Function Signature

```typescript
export async function fetchHoustonWeekly(url: string, days = 7): Promise<Permit[]>
```

## Features

- **Flexible Field Mapping**: Automatically detects various column name formats
  - Permit ID: `permitnumber`, `permitid`, `permit_no`
  - Issue Date: `issuedate`, `issue_date`, `dateissued`
  - Trade/Work Type: `worktype`, `tradetype`, `trade`
  - Address: `address`, `projectaddress`, `siteaddress`
  - ZIP Code: `zip`, `zipcode`, `postalcode`
  - Valuation: `valuation`, `jobvalue`
  - Contractor: `contractor`, `company`

- **Date Filtering**: Only returns permits issued within the specified number of days

- **Trade Normalization**: Automatically categorizes trades:
  - "elect*" → "Electrical"
  - "plumb*" → "Plumbing"
  - "mech*" → "Mechanical"
  - Others → "General"

- **Data Cleaning**: 
  - Removes currency symbols from valuation
  - Trims whitespace from text fields
  - Handles missing/null values gracefully

## Output Format

```typescript
interface Permit {
  source_system: "city_of_houston";
  permit_id: string;
  issue_date: string;  // ISO format
  trade: string;
  address?: string;
  zipcode?: string;
  valuation?: number | null;
  contractor?: string | null;
}
```

## Testing

Run tests to verify functionality:

```bash
# Basic test
npx tsx scripts/test_houstonWeekly.ts

# Core logic test
npx tsx scripts/test_houstonWeekly_core.ts

# Integration test
npx tsx scripts/test_houstonWeekly_integration.ts
```

## TypeScript Compatibility

All code is fully typed and passes TypeScript compilation:

```bash
npx tsc --noEmit scripts/houstonWeekly.ts scripts/supabaseSink.ts
```

## Implementation Notes

This is a "bulk starter" implementation that follows the exact specification from the problem statement, with minimal TypeScript fixes for compilation safety. It's designed to be a standalone adapter that can be easily integrated into existing permit processing workflows.