# Home-Services-Lead-Generation

Creating Leads For Home Service Contractors

## Overview

This repository provides tools and scrapers for generating leads for home service contractors by collecting and processing building permit data from various municipalities.

## Components

### Permit Leads Scraper (`permit_leads/`)

A comprehensive Python scraping pipeline that collects recent building permit data for the Houston, TX area and outputs normalized records in multiple formats (CSV, SQLite, JSONL).

**Key Features:**
- 🏠 **Houston-area Coverage**: Initially supports City of Houston with extensible architecture for additional municipalities
- 🔍 **Smart Filtering**: Automatically identifies and filters residential permits for contractor leads
- 📊 **Multiple Output Formats**: CSV, SQLite database, and JSONL for different use cases
- 🔄 **Deduplication**: Prevents duplicate records using permit ID and content hashing
- 🤖 **Polite Scraping**: Respects robots.txt, implements rate limiting, and polite delays
- 🧪 **Sample Data Support**: Test mode with realistic sample data for development
- ⚡ **CLI Interface**: Simple command-line interface with flexible options

**Quick Start:**
```bash
cd permit_leads
pip install -r requirements.txt

# Test with sample data
python -m permit_leads --source city_of_houston --sample --days 7

# Real scraping (when endpoints are configured)
python -m permit_leads --source city_of_houston --days 7 --formats csv sqlite
```

**Architecture:**
- `models/permit.py`: Pydantic-based data models with validation
- `scrapers/`: Scraper implementations (Houston City, extensible for others)
- `adapters/storage.py`: Handles CSV append and SQLite upsert operations
- `utils/`: HTTP utilities, normalization helpers, robots.txt checking
- `tests/`: Comprehensive test suite with sample data fixtures

See [`permit_leads/README.md`](permit_leads/README.md) for detailed documentation, usage examples, and extension instructions.

---

*Note: Always respect website terms of service and robots.txt when scraping. This tool is designed for ethical data collection with proper rate limiting and attribution.*
