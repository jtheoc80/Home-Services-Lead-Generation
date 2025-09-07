# Source-Agnostic Health Checks

Quick, copy/paste health checks for various data sources used in the Home Services Lead Generation platform. These can be run from your laptop or a GitHub Action shell step and will fail fast with clear reasons.

## Scripts

### 1. `scripts/source-health-checks.sh`
Full-featured health check script with error handling, logging, and multiple modes.

**Usage:**
```bash
./scripts/source-health-checks.sh [OPTIONS]

OPTIONS:
    --verbose       Show detailed curl output
    --test-urls     Use test URLs instead of production URLs  
    --help          Show help message

EXAMPLES:
    ./scripts/source-health-checks.sh                    # Run standard health checks
    ./scripts/source-health-checks.sh --verbose          # Run with detailed output
    ./scripts/source-health-checks.sh --test-urls        # Use test URLs for safe testing
```

### 2. `scripts/copy-paste-health-checks.sh`
Simple script containing the exact commands from the problem statement, ready to copy/paste.

**Usage:**
```bash
./scripts/copy-paste-health-checks.sh
```

## Health Check Types

### 1. DNS + TLS + HEAD (Connectivity & Status)
Tests basic connectivity to key data source domains:
- `https://www.houstontx.gov/planning/DevelopRegs/dev_reports.html`
- `https://data.austintexas.gov`
- `https://services.arcgis.com`
- `https://opendata.sanantonio.gov`
- `https://dallascityhall.com`

**What to look for:** HTTP/1.1 200 OK responses

### 2. ArcGIS Service Root Sanity
Tests ArcGIS FeatureServer/MapServer endpoints to ensure they return proper JSON service information.

**Example:**
```bash
ARC="https://your-arcgis-host/path/FeatureServer/0"
curl -sS "$ARC?f=pjson" | head -c 300
```

**What to look for:** JSON response with service metadata (name, type, geometryType)

### 3. ArcGIS Count Probe
Tests record count queries on ArcGIS services.

**Example:**
```bash
curl -sS "$ARC/query?where=1%3D1&returnCountOnly=true&f=json"
```

**What to look for:** JSON response with count field

### 4. Socrata API Probe
Tests Socrata APIs for Austin and San Antonio with App Token authentication.

**Environment Variables Required:**
```bash
export AUSTIN_SOCRATA_APP_TOKEN="your-austin-token"
export SA_SOCRATA_APP_TOKEN="your-sa-token"
```

**What to look for:** 
- JSON array with up to 1 row (success)
- 401/403 responses indicate missing/invalid App Token

### 5. Static XLSX Probe
Tests Houston Weekly permit file accessibility and content type.

**Example:**
```bash
curl -sSI "https://example.com/houston-weekly.xlsx" | egrep -i 'HTTP/|content-type|content-length'
```

**What to look for:** 
- HTTP/1.1 200 OK
- Content-Type: application/vnd.openxmlformats-officedocument.spreadsheetml.sheet

## Manual Copy/Paste Commands

For quick manual testing, you can copy/paste these individual commands:

### DNS + TLS + HEAD Check
```bash
for url in \
  "https://www.houstontx.gov/planning/DevelopRegs/dev_reports.html" \
  "https://data.austintexas.gov" \
  "https://services.arcgis.com" \
  "https://opendata.sanantonio.gov" \
  "https://dallascityhall.com"; do
  echo ">>> $url"
  getent ahosts "$(echo $url | awk -F/ '{print $3}')" || true
  curl -sS -I -A "LeadLedgerETL/1.0 (+github-actions)" "$url" | head -n 1
  echo
done
```

### ArcGIS Service Check
```bash
ARC="https://your-arcgis-host/path/FeatureServer/0"
curl -sS "$ARC?f=pjson" | head -c 300; echo
```

### ArcGIS Count Check
```bash
curl -sS "$ARC/query?where=1%3D1&returnCountOnly=true&f=json"
```

### Socrata Check
```bash
curl -sS "https://data.austintexas.gov/resource/RESOURCE_ID.json?\$limit=1" \
  -H "X-App-Token: $AUSTIN_SOCRATA_APP_TOKEN"

curl -sS "https://data.sanantonio.gov/resource/RESOURCE_ID.json?\$limit=1" \
  -H "X-App-Token: $SA_SOCRATA_APP_TOKEN"
```

### XLSX File Check
```bash
curl -sSI "WEEKLY_XLSX_URL" | egrep -i 'HTTP/|content-type|content-length'
```

## Testing

Run the test suite to validate all scripts work correctly:

```bash
./test-health-checks.sh
```

## Integration with CI/CD

These health checks can be easily integrated into GitHub Actions workflows:

```yaml
- name: Run Health Checks
  run: |
    ./scripts/source-health-checks.sh --verbose
  env:
    AUSTIN_SOCRATA_APP_TOKEN: ${{ secrets.AUSTIN_SOCRATA_APP_TOKEN }}
    SA_SOCRATA_APP_TOKEN: ${{ secrets.SA_SOCRATA_APP_TOKEN }}
```

## Expected Success Indicators

✅ **HTTP/1.1 200 OK** on HEAD requests  
✅ **ArcGIS ?f=pjson** returns JSON with service metadata  
✅ **ArcGIS query** returns JSON with count field  
✅ **Socrata** returns JSON array (401/403 = missing/invalid App Token)  
✅ **XLSX** has Content-Type: application/vnd.openxmlformats-officedocument.spreadsheetml.sheet  

## Troubleshooting

### DNS Resolution Failures
- Check network connectivity
- Verify domain names are correct
- Check firewall/proxy settings

### HTTP Errors
- 401/403: Authentication issues (check API tokens)
- 404: Incorrect URLs or endpoints
- 500: Server-side issues
- Timeouts: Network or server performance issues

### ArcGIS Issues
- Ensure URLs point to FeatureServer/MapServer endpoints, not HTML pages
- Check if service is public or requires authentication
- Verify service supports the f=pjson parameter

### Socrata Issues
- Verify App Tokens are set in environment variables
- Check if resource IDs are correct
- Ensure tokens have proper permissions