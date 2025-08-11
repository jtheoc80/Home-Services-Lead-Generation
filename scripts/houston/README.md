# Houston Permit Scrapers

This directory contains Houston-specific permit data scrapers.

## Modules

### `soldPermits.ts`

Placeholder implementation for scraping City of Houston "Sold Permits" data from the Houston Permitting Center.

**Status**: TODO - Implementation required

**Features**:
- TypeScript interfaces for Houston Sold Permits data structure
- Placeholder scraper class with configuration options
- TODO comments for both API and HTML scraping approaches
- Validation and parsing utilities

**Usage**:
```typescript
import { scrapeHoustonSoldPermits, HoustonSoldPermitsScraper } from './soldPermits.ts';

// Quick usage
const permits = await scrapeHoustonSoldPermits('2025-01-01', '2025-01-31');

// Advanced usage
const scraper = new HoustonSoldPermitsScraper({
  requestDelay: 1000,
  maxRetries: 5
});
const permits = await scraper.scrapePermits('2025-01-01', '2025-01-31');
```

**Implementation Notes**:
- Separate from Harris County unincorporated permits (County FeatureServer)
- Focuses specifically on City of Houston jurisdictional permits
- Requires research into Houston Permitting Center data sources
- Should check for API endpoints before falling back to HTML scraping

**TODO Items**:
1. Research Houston's data endpoints and API availability
2. Implement API-based fetching if available
3. Implement headless HTML scraping as fallback
4. Add proper error handling and retry mechanisms
5. Integrate with existing permit processing pipeline