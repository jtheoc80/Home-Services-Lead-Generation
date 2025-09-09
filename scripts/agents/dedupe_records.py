# Simple dedupe using dedupe_key if present; else fuzzy on address+zip with rapidfuzz.
# Usage: python scripts/agents/dedupe_records.py < artifacts/geocoded.ndjson > artifacts/final.ndjson
import sys
import json
from rapidfuzz import fuzz

rows = [json.loads(l) for l in sys.stdin]
group_id = 0
seen = {}
for i, r in enumerate(rows):
    key = r.get("dedupe_key")
    if key and key in seen:
        r["dupe_group_id"] = seen[key]
    elif key:
        group_id += 1
        seen[key] = group_id
        r["dupe_group_id"] = group_id
    else:
        # fallback: scan recent to find a near match
        matched = None
        for k, gid in list(seen.items())[-500:]:
            # compare end of key string; cheap fuzzy
            if fuzz.partial_ratio(k, (r.get("address") or "")[:60].lower()) > 92:
                matched = gid
                break
        if not matched:
            group_id += 1
            matched = group_id
        r["dupe_group_id"] = matched

for r in rows:
    print(json.dumps(r, ensure_ascii=False))
