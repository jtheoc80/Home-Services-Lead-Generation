# Normalize address_raw -> address, city, state, zipcode + dedupe_key (no external API needed)
# Usage: python scripts/agents/normalize_addresses.py < artifacts/parsed/source.ndjson > artifacts/normalized.ndjson
import sys
import json
import hashlib
import re
import usaddress


def clean(s):
    return re.sub(r"\s+", " ", (s or "")).strip()


for line in sys.stdin:
    row = json.loads(line)
    addr = clean(row.get("address_raw"))
    city = state = zip5 = ""
    street = ""

    if addr:
        try:
            tagged, _ = usaddress.tag(addr)
            street = " ".join(
                filter(
                    None,
                    [
                        tagged.get("AddressNumber"),
                        tagged.get("StreetNamePreType"),
                        tagged.get("StreetName"),
                        tagged.get("StreetNamePostType"),
                        tagged.get("OccupancyType"),
                        tagged.get("OccupancyIdentifier"),
                    ],
                )
            )
            city = tagged.get("PlaceName", "")
            state = (tagged.get("StateName", "") or "").upper()[:2]
            zip5 = (tagged.get("ZipCode", "") or "")[:5]
        except Exception:
            street = addr

    row["address"] = street or None
    row["city"] = city or row.get("city") or None
    row["state"] = state or row.get("state") or None
    row["zipcode"] = zip5 or (row.get("zipcode") or "")[:5] or None

    # Stable dedupe key
    key = f"{(row.get('address') or '').lower()}|{(row.get('zipcode') or '').lower()}|{(row.get('trade') or '').lower()}"
    row["dedupe_key"] = hashlib.md5(key.encode()).hexdigest()
    print(json.dumps(row, ensure_ascii=False))
