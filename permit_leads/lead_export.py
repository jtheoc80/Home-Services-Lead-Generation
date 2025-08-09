"""
Lead export & scoring utilities.

Provides:
- score_permit_rows: scoring logic for recent permits
- export_leads: orchestrator to read from SQLite and write scored CSVs
"""
from __future__ import annotations
import csv
import math
import sqlite3
from pathlib import Path
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Any, Tuple

# Fallback keywords (should eventually be centralized with normalization keywords)
RESIDENTIAL_FALLBACK_KEYWORDS = [
    "kitchen","bath","roof","remodel","addition","hvac","furnace","plumb","electrical",
    "siding","window","garage","deck","patio","pool","foundation"
]

# Work class / category weights (simple heuristic v1)
WORK_CLASS_WEIGHTS = {
    "ROOF": 12,
    "REMODEL": 15,
    "ADDITION": 18,
    "HVAC": 10,
    "MECHANICAL": 8,
    "PLUMBING": 8,
    "ELECTRICAL": 8,
    "POOL": 10,
}

SCORING_VERSION = "1.0.0"

LEAD_FIELD_ORDER = [
    "jurisdiction","permit_id","address","description","work_class","category",
    "status","issue_date","applicant","owner","value","is_residential","scraped_at",
    "score_total","score_recency","score_residential","score_value","score_work_class","scoring_version"
]

def _score_row(r: Dict[str, Any], now: datetime, lookback_days: int) -> Dict[str, Any]:
    # Parse issue date
    issue_raw = r.get("issue_date")
    issue_dt = None
    if issue_raw:
        try:
            issue_dt = datetime.fromisoformat(issue_raw)
        except Exception:
            pass

    # Recency score (linear decay)
    score_recency = 0.0
    if issue_dt:
        # Ensure timezone-aware comparison
        if issue_dt.tzinfo is None:
            issue_dt = issue_dt.replace(tzinfo=timezone.utc)
        delta_days = (now - issue_dt).days
        if 0 <= delta_days <= lookback_days:
            score_recency = round(25 * (1 - delta_days / lookback_days), 2)

    # Residential score
    is_res = r.get("is_residential") == 1
    desc = (r.get("description") or "").lower()
    work_class = (r.get("work_class") or "").lower()
    residential_hits = sum(1 for kw in RESIDENTIAL_FALLBACK_KEYWORDS if kw in desc or kw in work_class)
    score_residential = 20 if is_res else min(10, residential_hits * 2)

    # Value score (log-ish scaling)
    value_raw = r.get("value")
    try:
        value_f = float(value_raw) if value_raw is not None else 0.0
    except (ValueError, TypeError):
        value_f = 0.0
    score_value = 0.0
    if value_f > 0:
        # 5 * log10 scales: ~10k -> ~20, ~100k -> ~25 (capped)
        score_value = min(25, round(5 * math.log10(value_f + 10), 2))

    # Work class weight (take max matching key)
    wc_norm = (r.get("work_class") or "").upper()
    score_work_class = 0
    for key, wt in WORK_CLASS_WEIGHTS.items():
        if key in wc_norm:
            score_work_class = max(score_work_class, wt)

    total = round(score_recency + score_residential + score_value + score_work_class, 2)

    r.update(
        score_total=total,
        score_recency=score_recency,
        score_residential=score_residential,
        score_value=score_value,
        score_work_class=score_work_class,
        scoring_version=SCORING_VERSION,
    )
    return r

def score_permit_rows(rows: List[sqlite3.Row], lookback_days: int) -> List[Dict[str, Any]]:
    now = datetime.now(timezone.utc)
    scored = [_score_row(dict(r), now, lookback_days) for r in rows]
    scored.sort(key=lambda r: (r["score_total"], r.get("issue_date") or ""), reverse=True)
    return scored

def _write_csv(path: Path, rows: List[Dict[str, Any]]):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as f:
        if not rows:
            writer = csv.writer(f)
            writer.writerow(LEAD_FIELD_ORDER)
            return
        # Ensure consistent column order
        for r in rows:
            for col in LEAD_FIELD_ORDER:
                r.setdefault(col, "")
        writer = csv.DictWriter(f, fieldnames=LEAD_FIELD_ORDER)
        writer.writeheader()
        writer.writerows(rows)

def export_leads(
    db_path: Path,
    out_dir: Path,
    lookback_days: int,
    min_issue_date_only: bool = True
) -> Tuple[Path, int]:
    """Generate scored lead CSVs from the permits database.

    Returns:
        master_csv_path, count
    """
    if not db_path.exists():
        raise FileNotFoundError(f"Database not found: {db_path}")

    out_dir.mkdir(parents=True, exist_ok=True)
    per_jur_dir = out_dir / "by_jurisdiction"
    per_jur_dir.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row

    cutoff = (datetime.now(timezone.utc) - timedelta(days=lookback_days)).date().isoformat()

    where_clauses = ["issue_date >= ?"]
    params: List[Any] = [cutoff]

    if min_issue_date_only:
        pass

    query = f"""
        SELECT jurisdiction, permit_id, address, description, work_class, category,
               status, issue_date, applicant, owner, value, is_residential, scraped_at
        FROM permits
        WHERE {' AND '.join(where_clauses)}
    """

    rows = conn.execute(query, params).fetchall()
    scored = score_permit_rows(rows, lookback_days)

    master_csv = out_dir / "leads_recent.csv"
    _write_csv(master_csv, scored)

    # Per jurisdiction
    buckets: Dict[str, List[Dict[str, Any]]] = {}
    for r in scored:
        buckets.setdefault(r["jurisdiction"], []).append(r)

    for jur, jur_rows in buckets.items():
        fname = f"{jur.lower().replace(' ', '_')}_leads.csv"
        _write_csv(per_jur_dir / fname, jur_rows)

    return master_csv, len(scored)