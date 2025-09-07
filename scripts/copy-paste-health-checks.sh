#!/bin/bash
# =============================================================================
# Quick Copy/Paste Health Checks
# =============================================================================
# These are the exact commands from the problem statement, ready to copy/paste
# Run these from your laptop or a GH Action shell step.
# They'll fail fast with clear reasons.
# =============================================================================

echo "============================================================================="
echo "Quick, Source-Agnostic Health Checks (Copy/Paste Ready)"
echo "============================================================================="
echo "Run these commands individually or as a complete script."
echo "Look for: HTTP/1.1 200 OK, JSON responses, proper content types"
echo "============================================================================="
echo

# =============================================================================
# 1) DNS + TLS + HEAD (connectivity & status)
# =============================================================================
echo "# 1) DNS + TLS + HEAD (connectivity & status)"
echo "for url in \\"
echo '  "https://www.houstontx.gov/planning/DevelopRegs/dev_reports.html" \'
echo '  "https://data.austintexas.gov" \'
echo '  "https://services.arcgis.com" \'
echo '  "https://opendata.sanantonio.gov" \'
echo '  "https://dallascityhall.com"; do'
echo '  echo ">>> $url"'
echo '  getent ahosts "$(echo $url | awk -F/ '"'"'{print $3}'"'"')" || true'
echo '  curl -sS -I -A "LeadLedgerETL/1.0 (+github-actions)" "$url" | head -n 1'
echo '  echo'
echo 'done'
echo

echo "Executing DNS + TLS + HEAD checks..."
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

echo "============================================================================="
echo

# =============================================================================
# 2) ArcGIS service root sanity (returns JSON service info if correct base)
# =============================================================================
echo "# 2) ArcGIS service root sanity (returns JSON service info if correct base)"
echo "# Replace with your actual FeatureServer/MapServer URLs (NOT an HTML page)"
echo 'ARC="https://<arcgis-host>/<path>/FeatureServer/0"'
echo 'curl -sS "$ARC?f=pjson" | head -c 300; echo'
echo

echo "Example with a real ArcGIS service:"
ARC="https://sampleserver6.arcgisonline.com/arcgis/rest/services/Wildfire/FeatureServer/0"
echo "ARC=\"$ARC\""
echo "curl -sS \"\$ARC?f=pjson\" | head -c 300; echo"
curl -sS "$ARC?f=pjson" | head -c 300; echo
echo

echo "============================================================================="
echo

# =============================================================================
# 3) ArcGIS count probe (date filter optional)
# =============================================================================
echo "# 3) ArcGIS count probe (date filter optional)"
echo 'curl -sS "$ARC/query?where=1%3D1&returnCountOnly=true&f=json"'
echo

echo "Executing ArcGIS count probe..."
curl -sS "$ARC/query?where=1%3D1&returnCountOnly=true&f=json"
echo
echo

echo "============================================================================="
echo

# =============================================================================
# 4) Socrata probe (Austin / San Antonio) – needs App Tokens
# =============================================================================
echo "# 4) Socrata probe (Austin / San Antonio) – needs App Tokens"
echo "# Replace resource id; set envs AUSTIN_SOCRATA_APP_TOKEN / SA_SOCRATA_APP_TOKEN"
echo 'curl -sS "https://data.austintexas.gov/resource/<RESOURCE_ID>.json?\$limit=1" \'
echo '  -H "X-App-Token: $AUSTIN_SOCRATA_APP_TOKEN"'
echo
echo 'curl -sS "https://data.sanantonio.gov/resource/<RESOURCE_ID>.json?\$limit=1" \'
echo '  -H "X-App-Token: $SA_SOCRATA_APP_TOKEN"'
echo

echo "Testing Socrata APIs (requires tokens)..."
if [ -n "${AUSTIN_SOCRATA_APP_TOKEN:-}" ]; then
    echo "Austin Socrata test:"
    curl -sS "https://data.austintexas.gov/resource/3syk-w9eu.json?\$limit=1" \
      -H "X-App-Token: $AUSTIN_SOCRATA_APP_TOKEN" | head -c 200
    echo
else
    echo "⚠️  AUSTIN_SOCRATA_APP_TOKEN not set - skipping Austin test"
fi

if [ -n "${SA_SOCRATA_APP_TOKEN:-}" ]; then
    echo "San Antonio Socrata test:"
    curl -sS "https://data.sanantonio.gov/resource/<RESOURCE_ID>.json?\$limit=1" \
      -H "X-App-Token: $SA_SOCRATA_APP_TOKEN" | head -c 200
    echo
else
    echo "⚠️  SA_SOCRATA_APP_TOKEN not set - skipping San Antonio test"
fi

echo
echo "============================================================================="
echo

# =============================================================================
# 4b) Austin Socrata Manual Testing (from problem statement)
# =============================================================================
echo "# 4b) Austin Socrata Manual Testing (from problem statement)"
echo "# set your token and dataset id (find on the dataset's API page)"
echo 'export AUSTIN_SOCRATA_APP_TOKEN=YOUR_TOKEN'
echo 'export AUSTIN_DATASET_ID=abcd-1234   # <-- replace with the real resource id'
echo
echo '# HEAD check (portal reachable)'
echo 'curl -sS -I https://data.austintexas.gov | head -n1'
echo
echo '# 1 sample row (should print a small JSON array)'
echo 'curl -sS "https://data.austintexas.gov/resource/$AUSTIN_DATASET_ID.json?\$limit=1" \'
echo '  -H "X-App-Token: $AUSTIN_SOCRATA_APP_TOKEN"'
echo
echo '# download a CSV (no code)'
echo 'START=2024-01-01'
echo 'curl -sS "https://data.austintexas.gov/resource/$AUSTIN_DATASET_ID.csv?\'
echo '\$where=issued_date >= '"'"'$START'"'"'&\$order=issued_date&\$limit=50000" \'
echo '  -H "X-App-Token: $AUSTIN_SOCRATA_APP_TOKEN" \'
echo '  -o austin_sample.csv'
echo 'wc -l austin_sample.csv && head -5 austin_sample.csv'
echo

echo "Austin Manual Testing (if tokens are set)..."
if [ -n "${AUSTIN_SOCRATA_APP_TOKEN:-}" ] && [ -n "${AUSTIN_DATASET_ID:-}" ]; then
    echo "Executing Austin manual testing commands..."
    
    echo ">>> HEAD check"
    curl -sS -I https://data.austintexas.gov | head -n1
    echo
    
    echo ">>> Sample row"
    curl -sS "https://data.austintexas.gov/resource/$AUSTIN_DATASET_ID.json?\$limit=1" \
      -H "X-App-Token: $AUSTIN_SOCRATA_APP_TOKEN" | head -c 300
    echo
    echo
    
    echo ">>> CSV download test (limited to 10 rows for demo)"
    START=2024-01-01
    curl -sS "https://data.austintexas.gov/resource/$AUSTIN_DATASET_ID.csv?\$where=issued_date >= '$START'&\$order=issued_date&\$limit=10" \
      -H "X-App-Token: $AUSTIN_SOCRATA_APP_TOKEN" \
      -o austin_sample_demo.csv 2>/dev/null
    
    if [ -f austin_sample_demo.csv ]; then
        echo "Demo CSV created with $(wc -l < austin_sample_demo.csv) lines"
        echo "First 3 lines:"
        head -3 austin_sample_demo.csv
        rm -f austin_sample_demo.csv
    else
        echo "CSV download failed"
    fi
else
    echo "⚠️  AUSTIN_SOCRATA_APP_TOKEN and/or AUSTIN_DATASET_ID not set - skipping Austin manual test"
    echo "   Use: ./scripts/austin-socrata-manual-test.sh for full Austin testing"
fi

echo
echo "============================================================================="
echo

# =============================================================================
# 5) Static XLSX probe (Houston Weekly) – verify it's a real file
# =============================================================================
echo "# 5) Static XLSX probe (Houston Weekly) – verify it's a real file"
echo 'curl -sSI "<WEEKLY_XLSX_URL>" | egrep -i '"'"'HTTP/|content-type|content-length'"'"''
echo

echo "Example XLSX header check (replace URL with actual Houston Weekly URL):"
echo "curl -sSI \"https://example.com/houston-weekly.xlsx\" | egrep -i 'HTTP/|content-type|content-length'"
echo

echo "============================================================================="
echo "What to look for:"
echo "============================================================================="
echo "✅ HTTP/1.1 200 OK on HEADs."
echo "✅ ArcGIS ?f=pjson returns JSON; /query?...returnCountOnly=true returns a JSON with count."
echo "✅ Socrata returns a JSON array with up to 1 row (401/403 ⇒ missing/invalid App Token)."
echo "✅ XLSX has Content-Type: application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
echo "============================================================================="