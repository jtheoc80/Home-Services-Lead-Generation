# Light parser for XLS/XLSX/CSV/HTML into NDJSON.
# Usage: python scripts/agents/parse_unstructured.py <input_path> <source_name> > artifacts/parsed/<source>.ndjson
import sys
import json
import pandas as pd
from pathlib import Path

inp = Path(sys.argv[1]) if len(sys.argv) > 1 else None
source = sys.argv[2] if len(sys.argv) > 2 else "unknown_source"
if not inp or not inp.exists():
    raise SystemExit("Usage: parse_unstructured.py <input_path> <source_name>")

df = None
suffix = inp.suffix.lower()
if suffix in [".xlsx", ".xls"]:
    df = pd.read_excel(inp, dtype=str)
elif suffix in [".csv"]:
    df = pd.read_csv(inp, dtype=str)
elif suffix in [".htm", ".html"]:
    tables = pd.read_html(inp.read_text(encoding="utf-8", errors="ignore"))
    df = tables[0] if tables else pd.DataFrame()
else:
    raise SystemExit(
        f"Unsupported file type: {suffix}. For PDFs or others, add unstructured later."
    )

df = df.fillna("")
for _, r in df.iterrows():
    row = r.to_dict()
    # Try to standardize the obvious fields into a raw shell the next agents expect
    out = {
        "source": source,
        "external_permit_id": str(
            row.get("PERMIT_NO")
            or row.get("Permit #")
            or row.get("PERMIT")
            or row.get("NUMBER")
            or ""
        ),
        "issued_date": row.get("ISSUED_DATE")
        or row.get("Issue Date")
        or row.get("ISSUED")
        or "",
        "trade": row.get("TRADE")
        or row.get("Permit Type")
        or row.get("permit_type")
        or "",
        "address_raw": row.get("ADDRESS")
        or row.get("SITE_ADDR")
        or row.get("Address")
        or row.get("location")
        or "",
        "zipcode": str(
            row.get("ZIP")
            or row.get("Zip")
            or row.get("ZIPCODE")
            or row.get("zip")
            or ""
        ),
        "raw": row,
    }
    print(json.dumps(out, ensure_ascii=False))
