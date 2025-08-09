# Permit Leads Scraper

Collect recent *residential* building permits from local government sites and package them as contractor leads.

## What it does

- Pulls permits from city open-data portals (Socrata) or simple HTML tables
- Normalizes fields (address, description, contractor, cost, etc.)
- Filters for likely residential work (configurable keywords)
- Saves to **SQLite** and **CSV**
- Respects **robots.txt** and rate-limits requests

> ⚠️ Always verify each site's **Terms of Use** and **robots.txt**. Prefer official APIs (e.g., Socrata, Accela). Some jurisdictions prohibit scraping; get permission if unsure.

## Quick start

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python main.py --days 30 --outdir out
```

This ships with a working example for **Chicago** (`Socrata`) and a placeholder HTML-table source to show how to add non-API sites.

Outputs:
- `out/permits.sqlite`
- `out/permits.csv`

## Adding your cities

1. **Socrata (preferred)**
   - Find the city's open data portal (often `data.cityname.gov`).
   - Locate the Building Permits dataset and copy the **dataset identifier** (four-four like `xxxx-xxxx`).
   - In `config/sources.yaml`, add:
     ```yaml
     - name: My City Permits
       type: socrata
       domain: data.mycity.gov
       dataset_id: abcd-1234
       date_field: issue_date   # adjust to the portal's field
       mappings:
         permit_number: "permit_no"
         address: "street_address"
         description: "work_description"
         applicant: "applicant_name"
         status: "status"
         value: "declared_valuation"
         latitude: "latitude"
         longitude: "longitude"
         work_class: "permit_type"
         category: "permit_type"
     ```

2. **Accela (many cities use it)**
   - Prefer their **open-data feeds** if provided. Direct Accela API access may require API keys.
   - Implement a dedicated adapter if needed (patterned after `socrata_adapter.py`).

3. **HTML pages (last resort)**
   - Add a block using `type: html_table` and set `url` + `table_selector`.
   - You may need to customize parsing depending on the page structure.

## Residential filtering

Basic keyword filter lives in `utils/normalize.py` (`RESIDENTIAL_KEYWORDS`). Tweak it per market (e.g., add "bath", "shower", "roof", "addition", etc.).

## Packaging leads

Once collected, you can:
- Export CSV and send to contractors weekly
- Segment by ZIP, work type, estimated value
- Enrich with geocoding / parcel data (add later)

## CLI options

```
python main.py --help
```

Key flags:
- `--days 30` : look back window
- `--limit 5000` : per-source cap
- `--outdir out` : where to store SQLite/CSV
- `--user_agent "YourCompanyLeadBot/1.0 (you@domain.com)"`

## Extending

- Add de-dup + scoring logic in `utils/storage.py`
- Build a small Flask API or Streamlit dashboard on top of `permits.sqlite`
- Add SMTP to email top leads to your contractor list

## Legal/Ethical

- Respect `robots.txt`
- Honor terms of service & rate limits
- Provide attribution when required by the data license
