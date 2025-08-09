# Houston-Area Permit Leads Scraper

A reusable Python scraping pipeline that collects recent building permit data for the Houston, TX area and outputs normalized records in multiple formats. Designed with an extensible architecture for adding additional municipalities.

## 🚀 Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Test with sample data
python -m permit_leads --source city_of_houston --sample --days 7 --formats csv sqlite

# See all options
python -m permit_leads --help
```

## 📊 What it does

- **Collects** building permits from Houston-area municipal systems
- **Normalizes** permit data (address, description, contractor, value, etc.)
- **Filters** for residential projects likely to need contractor services
- **Outputs** data in CSV, SQLite, and JSONL formats with deduplication
- **Respects** robots.txt and implements polite scraping practices

## 🏗️ Architecture

### Core Components

- **`models/permit.py`**: Pydantic-based PermitRecord model with validation and normalization
- **`scrapers/`**: Scraper implementations using abstract base class pattern
  - `base.py`: Common HTTP utilities, rate limiting, retry logic
  - `houston_city.py`: City of Houston permit scraper with sample data support
- **`adapters/storage.py`**: Handles writing to CSV (append) and SQLite (upsert) with deduplication
- **`utils/`**: Supporting utilities for HTTP, normalization, robots.txt checking
- **`samples/`**: Sample HTML/JSON data for testing scrapers offline
- **`tests/`**: Comprehensive test suite with fixtures

### Data Flow

```
Web Source → Scraper → PermitRecord → Storage Adapter → CSV/SQLite/JSONL
```

## 📋 CLI Usage

### Basic Commands

```bash
# Scrape specific source with sample data
python -m permit_leads --source city_of_houston --sample

# Real scraping with multiple formats
python -m permit_leads --source city_of_houston --days 7 --formats csv sqlite jsonl

# Run all configured scrapers
python -m permit_leads --all --days 30

# Dry run (parse but don't save)
python -m permit_leads --source city_of_houston --sample --dry-run
```

### CLI Options

| Option | Description | Default |
|--------|-------------|---------|
| `--source` | Specific scraper to run | - |
| `--all` | Run all available scrapers | - |
| `--days` | Look-back window in days | 7 |
| `--limit` | Max records per source | None |
| `--formats` | Output formats: csv, sqlite, jsonl | csv sqlite |
| `--output-dir` | Output directory | data |
| `--sample` | Use sample data instead of live scraping | False |
| `--dry-run` | Parse but don't persist data | False |
| `--verbose` | Enable debug logging | False |
| `--sleep` | Delay between requests (seconds) | 2.0 |

## 📁 Output Structure

```
data/
├── permits/
│   ├── raw/
│   │   └── city_of_houston/
│   │       └── 2025-08-09.jsonl
│   ├── aggregate/
│   │   ├── permits_2025-08-09.csv
│   │   └── permits_latest.csv
│   └── permits.db
```

- **Raw JSONL**: Daily files per jurisdiction with full normalized records
- **Aggregate CSV**: Date-stamped files plus `permits_latest.csv` symlink
- **SQLite Database**: Central database with deduplication and full-text search

## 🔧 Data Model

### PermitRecord Fields

| Field | Type | Description |
|-------|------|-------------|
| `jurisdiction` | str | Source municipality name |
| `permit_id` | str | Permit number/ID |
| `address` | str | Full street address |
| `description` | str | Work description |
| `work_class` | str | Permit type/category |
| `category` | str | residential/commercial/other |
| `status` | str | Permit status |
| `issue_date` | datetime | Date permit was issued |
| `applicant` | str | Applicant/contractor name |
| `value` | float | Declared project value |
| `extra_data` | dict | Additional source-specific fields |

### Residential Classification

Permits are automatically classified as residential based on:
- Permit type containing "residential", "single family", "duplex"
- Work descriptions mentioning "kitchen", "bathroom", "roof", "addition", etc.
- Configurable keyword lists in `utils/normalize.py`

## 🏙️ Adding New Municipalities

### 1. Create New Scraper

```python
# scrapers/my_city.py
from scrapers.base import BaseScraper
from models.permit import PermitRecord

class MyCityScraper(BaseScraper):
    def __init__(self):
        super().__init__(
            jurisdiction="My City",
            base_url="https://permits.mycity.gov/"
        )
    
    def fetch_permits(self, since, limit=None):
        # Implement data fetching
        pass
    
    def parse_permit(self, raw_data):
        # Return PermitRecord object
        pass
```

### 2. Register Scraper

Add to `main.py`:
```python
from scrapers.my_city import MyCityScraper

SCRAPERS = {
    "city_of_houston": HoustonCityScraper,
    "my_city": MyCityScraper,  # Add here
}
```

### 3. Create Sample Data

```html
<!-- samples/my_city/sample_listing.html -->
<table>
  <tr><th>Permit #</th><th>Address</th>...</tr>
  <tr><td>12345</td><td>123 Main St</td>...</tr>
</table>
```

### 4. Add Tests

```python
# tests/test_my_city.py
def test_my_city_scraper():
    scraper = MyCityScraper()
    permits = scraper.scrape_permits(since=datetime.now())
    assert len(permits) > 0
```

## 🔒 Ethical Scraping

### IMPORTANT NOTICE

- **Respect robots.txt**: Always check and honor robots.txt directives
- **Rate limiting**: Built-in delays between requests (default 2 seconds)
- **Terms of Service**: Review and comply with each site's terms
- **Attribution**: Provide proper attribution when required by data licenses
- **Permission**: Get explicit permission when in doubt

### Best Practices

- Use `--sample` mode for development and testing
- Start with small `--days` values when testing live endpoints
- Monitor logs for rate limiting and error patterns
- Prefer official APIs over HTML scraping when available

## 🧪 Testing

```bash
# Run all tests
python -m pytest tests/ -v

# Test specific scraper
python -m pytest tests/test_houston_city.py -v

# Test with coverage
python -m pytest tests/ --cov=. --cov-report=html
```

## 📈 Extending Features

### Lead Scoring
Add scoring logic in `models/permit.py`:
```python
def get_lead_score(self) -> float:
    score = 0.0
    if self.value and self.value > 50000:
        score += 0.3
    if 'renovation' in self.description.lower():
        score += 0.2
    return score
```

### Geocoding
Enhance addresses with coordinates:
```python
# utils/geocoding.py
def geocode_address(address: str) -> Tuple[float, float]:
    # Implement geocoding service integration
    pass
```

### Lead Export
Generate contractor-friendly exports:
```python
# utils/export.py
def export_weekly_leads(output_file: str):
    # Create formatted lead sheets
    pass
```

## 🔧 Troubleshooting

### Common Issues

**Import Errors**: Ensure you're running from the correct directory
```bash
cd permit_leads
python -m pytest tests/
```

**No Permits Found**: Check date range and sample data mode
```bash
python -m permit_leads --source city_of_houston --sample --verbose
```

**Network Errors**: Verify network connectivity and robots.txt
```bash
python -m permit_leads --source city_of_houston --no-robots --sample
```

### Development Mode

```bash
# Install in development mode
pip install -e .

# Run with debug logging
python -m permit_leads --source city_of_houston --verbose --sample
```

---

## 📄 License

See [LICENSE](../LICENSE) for terms of use.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass
5. Submit a pull request

---

*Built with ❤️ for the home services industry. Always scrape responsibly.*
