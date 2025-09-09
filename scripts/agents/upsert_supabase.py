# Bulk upsert NDJSON into Supabase 'permits', then call RPC to mint leads.
# Usage: python scripts/agents/upsert_supabase.py artifacts/final.ndjson
# Requires secrets: SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY
import os, sys, json, requests

SUPABASE_URL = os.environ["SUPABASE_URL"]
SRK          = os.environ["SUPABASE_SERVICE_ROLE_KEY"]

if len(sys.argv) < 2: raise SystemExit("Usage: upsert_supabase.py <ndjson_path>")
path = sys.argv[1]

rows = []
with open(path, "r", encoding="utf-8") as f:
    for line in f:
        row = json.loads(line)
        rows.append({
            "source": row.get("source"),
            "external_permit_id": row.get("external_permit_id"),
            "issued_date": row.get("issued_date") or None,
            "trade": row.get("trade") or None,
            "address": row.get("address") or row.get("address_raw") or None,
            "zipcode": (row.get("zipcode") or "")[:5] or None,
            "county": row.get("county") or row.get("jurisdiction") or None,
            "jurisdiction": row.get("jurisdiction") or None,
            "lat": row.get("lat"), "lon": row.get("lon"),
            "raw": row.get("raw") or row
        })

headers = {
  "apikey": SRK,
  "Authorization": f"Bearer {SRK}",
  "Content-Type": "application/json",
  "Prefer": "resolution=merge-duplicates"  # requires unique (source, external_permit_id)
}

# chunked upsert (PostgREST likes smaller bodies)
def chunks(lst, n): 
    for i in range(0, len(lst), n): 
        yield lst[i:i+n]

upsert_url = f"{SUPABASE_URL}/rest/v1/permits"
total = 0
for chunk in chunks(rows, 500):
    r = requests.post(upsert_url, headers=headers, json=chunk, timeout=60)
    if r.status_code >= 300:
        raise SystemExit(f"Upsert failed: {r.status_code} {r.text}")
    total += len(chunk)

# Call RPC to create leads
rpc_url = f"{SUPABASE_URL}/rest/v1/rpc/upsert_leads_from_permits_limit"
rpc = requests.post(rpc_url, headers=headers, json={"p_limit": 50, "p_days": 365}, timeout=60)
if rpc.status_code >= 300:
    raise SystemExit(f"RPC failed: {rpc.status_code} {rpc.text}")

print(json.dumps({"upserted": total, "leads_created": rpc.json()}, ensure_ascii=False))