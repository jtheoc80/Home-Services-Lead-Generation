#!/usr/bin/env python3
import argparse
import datetime as dt
import json
from pathlib import Path
import sys
from typing import List, Dict, Any

from utils.storage import Storage
from utils.normalize import normalize_record, RESIDENTIAL_KEYWORDS
from utils.robots import PoliteSession
from adapters.socrata_adapter import SocrataAdapter
from adapters.html_table_adapter import HTMLTableAdapter
from adapters.arcgis_feature_service import ArcGISFeatureServiceAdapter
from adapters.accela_html_adapter import AccelaHTMLAdapter

ADAPTERS = {
    "socrata": SocrataAdapter,
    "html_table": HTMLTableAdapter,
    "arcgis_feature_service": ArcGISFeatureServiceAdapter,
    "accela_html": AccelaHTMLAdapter,
}


def load_sources(config_path: Path) -> List[Dict[str, Any]]:
    import yaml

    with open(config_path, "r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)
    return cfg.get("sources", [])


def run_source(source_cfg, session, days, limit, storage):
    name = source_cfg.get("name", "unknown")
    adapter_type = source_cfg["type"]
    adapter_cls = ADAPTERS.get(adapter_type)
    if not adapter_cls:
        print(
            f"[WARN] Unsupported adapter type: {adapter_type} for {name}",
            file=sys.stderr,
        )
        return

    adapter = adapter_cls(source_cfg, session=session)

    since = dt.datetime.utcnow() - dt.timedelta(days=days)
    raw_records = adapter.fetch_since(since=since, limit=limit)

    count_in = 0
    count_res = 0
    count_saved = 0
    for rec in raw_records:
        count_in += 1
        rec_norm = normalize_record(rec, source=name)
        # Pass 1: if adapter says it's residential, accept
        is_residential = rec_norm.get("category", "").lower() == "residential"
        # Pass 2: keyword fallback
        text_blob = " ".join(
            [
                str(rec_norm.get(k, ""))
                for k in ["description", "work_class", "permit_type"]
            ]
        ).lower()
        kw_hit = any(kw in text_blob for kw in RESIDENTIAL_KEYWORDS)
        if is_residential or kw_hit:
            count_res += 1
            saved = storage.save(rec_norm)
            if saved:
                count_saved += 1

    print(
        f"[{name}] pulled={count_in} residential_like={count_res} saved={count_saved}"
    )


def main():
    ap = argparse.ArgumentParser(
        description="Scrape/collect building permits for residential projects and export as contractor leads."
    )
    ap.add_argument(
        "--config",
        default="config/sources.yaml",
        help="Path to YAML config of sources.",
    )
    ap.add_argument("--days", type=int, default=30, help="Look-back window in days.")
    ap.add_argument("--limit", type=int, default=5000, help="Max records per source.")
    ap.add_argument("--outdir", default="out", help="Output directory for CSV/SQLite.")
    ap.add_argument(
        "--db", default="permits.sqlite", help="SQLite db filename inside outdir."
    )
    ap.add_argument("--csv", default="permits.csv", help="CSV filename inside outdir.")
    ap.add_argument(
        "--user_agent",
        default="PermitLeadBot/1.0 (+contact@example.com)",
        help="User-Agent for polite scraping.",
    )
    args = ap.parse_args()

    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    storage = Storage(db_path=outdir / args.db, csv_path=outdir / args.csv)

    session = PoliteSession(user_agent=args.user_agent)

    sources = load_sources(Path(args.config))
    if not sources:
        print("[ERROR] No sources configured. See config/sources.yaml", file=sys.stderr)
        sys.exit(1)

    for src in sources:
        try:
            run_source(src, session, days=args.days, limit=args.limit, storage=storage)
        except Exception as e:
            print(f"[ERROR] {src.get('name','unknown')}: {e}", file=sys.stderr)

    # show small summary
    print("\nTop 10 newest saved permits:")
    for row in storage.latest(10):
        print(json.dumps(row, default=str))


if __name__ == "__main__":
    main()
