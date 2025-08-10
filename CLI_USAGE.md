# Permit Leads CLI Usage

## Quick Start: Sample Mode for Last 7 Days

To run the scraper in sample mode for the last 7 days and write CSV to `permit_leads/out/leads_recent.csv`:

```bash
# Step 1: Scrape permits and store in database
python -m permit_leads --source city_of_houston --sample --days 7 --formats sqlite

# Step 2: Export leads from database to desired location
python -m permit_leads export-leads --lookback 7 --out permit_leads/out
```

**Single command line version:**
```bash
python -m permit_leads --source city_of_houston --sample --days 7 --formats sqlite && python -m permit_leads export-leads --lookback 7 --out permit_leads/out
```

## What this does:

1. **Scraping**: Uses sample permit data from Houston City to simulate scraping permits from the last 7 days
2. **Storage**: Stores the permits in SQLite database format at `data/permits/permits.db`
3. **Lead Export**: Converts permits to scored leads and exports to `permit_leads/out/leads_recent.csv`

## Output:

- Main leads file: `permit_leads/out/leads_recent.csv` (scored residential permits suitable for lead generation)
- Per-jurisdiction file: `permit_leads/out/by_jurisdiction/city_of_houston_leads.csv`

## CLI Parameters Explained:

- `--source city_of_houston`: Use the Houston City scraper
- `--sample`: Use sample/fixture data instead of live scraping  
- `--days 7`: Look back 7 days from today
- `--formats sqlite`: Output to SQLite database (required for lead export)
- `export-leads --lookback 7`: Export leads from permits issued in last 7 days
- `--out permit_leads/out`: Output directory for the leads CSV files

## Full CLI Help:

```bash
python -m permit_leads --help
python -m permit_leads export-leads --help
```