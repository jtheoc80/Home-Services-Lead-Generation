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