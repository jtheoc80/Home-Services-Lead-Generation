"""
Enhanced lead export & scoring with enrichment integration.

Extends the original lead_export.py with enrichment pipeline integration
and improved scoring based on enriched data.
"""
from __future__ import annotations
import csv
import math
import sqlite3
from pathlib import Path
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Any, Tuple
from .enrich import enrich_record

# Enhanced scoring weights for enriched data
SCORING_WEIGHTS = {
    'recency': 3.0,      # Recency is most important
    'trade_match': 2.0,  # Trade relevance 
    'value': 2.0,        # Project value
    'parcel_age': 1.0,   # Older homes bonus
    'inspection': 1.0    # Inspection status bonus
}

SCORING_VERSION = "2.0.0"

# Enhanced field order including enriched fields
ENRICHED_LEAD_FIELD_ORDER = [
    # Core permit fields
    "jurisdiction", "permit_id", "address", "description", "work_class", "category",
    "status", "issue_date", "applicant", "owner", "value", "is_residential", "scraped_at",
    
    # Enriched location fields  
    "latitude", "longitude",
    
    # Enriched parcel fields
    "apn", "year_built", "heated_sqft", "lot_size", "land_use",
    
    # Enriched classification fields
    "owner_kind", "trade_tags", "budget_band", "start_by_estimate",
    
    # Enhanced scoring fields
    "lead_score", "score_recency", "score_trade_match", "score_value", 
    "score_parcel_age", "score_inspection", "scoring_version"
]


def compute_enhanced_score(record: Dict[str, Any], now: datetime, lookback_days: int) -> Dict[str, Any]:
    """
    Compute enhanced lead score using enriched data.
    
    Scoring components:
    - Recency (0-25 points, weight 3x) 
    - Trade match (0-25 points, weight 2x)
    - Value/budget (0-25 points, weight 2x)
    - Parcel age bonus (0-10 points, weight 1x)
    - Inspection status (0-10 points, weight 1x)
    
    Final score capped at 100.
    """
    # 1. Recency score (25 points max)
    score_recency = _compute_recency_score(record, now, lookback_days)
    
    # 2. Trade match score (25 points max)
    score_trade_match = _compute_trade_score(record)
    
    # 3. Value score (25 points max)
    score_value = _compute_value_score(record)
    
    # 4. Parcel age bonus (10 points max)
    score_parcel_age = _compute_parcel_age_score(record)
    
    # 5. Inspection status bonus (10 points max)
    score_inspection = _compute_inspection_score(record)
    
    # Apply weights and compute total
    weighted_total = (
        score_recency * SCORING_WEIGHTS['recency'] +
        score_trade_match * SCORING_WEIGHTS['trade_match'] +
        score_value * SCORING_WEIGHTS['value'] +
        score_parcel_age * SCORING_WEIGHTS['parcel_age'] + 
        score_inspection * SCORING_WEIGHTS['inspection']
    )
    
    # Cap to 100 and round
    lead_score = min(100, round(weighted_total, 1))
    
    # Update record with scores
    record.update({
        'lead_score': lead_score,
        'score_recency': score_recency,
        'score_trade_match': score_trade_match,
        'score_value': score_value,
        'score_parcel_age': score_parcel_age,
        'score_inspection': score_inspection,
        'scoring_version': SCORING_VERSION
    })
    
    return record


def _compute_recency_score(record: Dict[str, Any], now: datetime, lookback_days: int) -> float:
    """Compute recency score (0-25 points)."""
    issue_raw = record.get('issue_date')
    if not issue_raw:
        return 0.0
        
    try:
        issue_dt = datetime.fromisoformat(issue_raw.replace('Z', '+00:00'))
        if issue_dt.tzinfo is None:
            issue_dt = issue_dt.replace(tzinfo=timezone.utc)
            
        delta_days = (now - issue_dt).days
        if 0 <= delta_days <= lookback_days:
            # Linear decay: newest permits get full 25 points
            return round(25.0 * (1 - delta_days / lookback_days), 2)
    except Exception:
        pass
    
    return 0.0


def _compute_trade_score(record: Dict[str, Any]) -> float:
    """Compute trade relevance score (0-25 points)."""
    trade_tags = record.get('trade_tags', [])
    if not trade_tags:
        return 0.0
    
    # High-value trades get higher scores
    trade_values = {
        'roofing': 25,
        'kitchen': 24, 
        'bath': 22,
        'hvac': 20,
        'pool': 18,
        'foundation': 16,
        'electrical': 14,
        'plumbing': 14,
        'windows': 12,
        'solar': 20,
        'fence': 8
    }
    
    # Take maximum score from matched trades
    max_score = 0
    for tag in trade_tags:
        if tag in trade_values:
            max_score = max(max_score, trade_values[tag])
    
    return float(max_score)


def _compute_value_score(record: Dict[str, Any]) -> float:
    """Compute project value score (0-25 points)."""
    value = record.get('value')
    if not value or value <= 0:
        return 0.0
    
    try:
        value_f = float(value)
        # Logarithmic scaling: $1k->5pts, $10k->15pts, $100k->25pts
        score = min(25.0, 5.0 * math.log10(value_f / 1000 + 1))
        return round(score, 2)
    except (ValueError, TypeError):
        return 0.0


def _compute_parcel_age_score(record: Dict[str, Any]) -> float:
    """Compute parcel age bonus (0-10 points). Older homes more likely to need work."""
    year_built = record.get('year_built')
    if not year_built:
        return 0.0
    
    try:
        current_year = datetime.now().year
        age = current_year - int(year_built)
        
        # Homes 15+ years old get bonus points
        if age >= 40:
            return 10.0  # Very old homes
        elif age >= 25:
            return 7.0   # Older homes
        elif age >= 15:
            return 4.0   # Moderately old homes
        else:
            return 0.0   # New homes
    except (ValueError, TypeError):
        return 0.0


def _compute_inspection_score(record: Dict[str, Any]) -> float:
    """Compute inspection status bonus (0-10 points)."""
    status = record.get('status', '').lower()
    
    if 'approved' in status or 'issued' in status:
        return 10.0  # Ready to proceed
    elif 'review' in status or 'pending' in status:
        return 5.0   # In process
    elif 'applied' in status or 'submitted' in status:
        return 2.0   # Early stage
    else:
        return 0.0


def export_enriched_leads(
    db_path: Path,
    out_dir: Path,
    lookback_days: int,
    enrich_data: bool = True
) -> Tuple[Path, int]:
    """
    Generate scored lead CSVs with enrichment.
    
    Args:
        db_path: Path to permits SQLite database
        out_dir: Output directory for CSV files
        lookback_days: Number of days to look back
        enrich_data: Whether to run enrichment pipeline
        
    Returns:
        (master_csv_path, record_count)
    """
    if not db_path.exists():
        raise FileNotFoundError(f"Database not found: {db_path}")

    out_dir.mkdir(parents=True, exist_ok=True)
    per_jur_dir = out_dir / "by_jurisdiction"
    per_jur_dir.mkdir(parents=True, exist_ok=True)

    # Connect to database
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row

    cutoff = (datetime.now(timezone.utc) - timedelta(days=lookback_days)).date().isoformat()

    # Query permits
    query = """
        SELECT jurisdiction, permit_id, address, description, work_class, category,
               status, issue_date, applicant, owner, value, is_residential, scraped_at,
               latitude, longitude, apn, year_built, heated_sqft, lot_size, land_use,
               owner_kind, trade_tags, budget_band, start_by_estimate
        FROM permits 
        WHERE issue_date >= ?
    """

    rows = conn.execute(query, [cutoff]).fetchall()
    
    # Convert to dicts and optionally enrich
    records = []
    now = datetime.now(timezone.utc)
    
    for row in rows:
        record = dict(row)
        
        # Parse JSON fields if present
        if record.get('trade_tags') and isinstance(record['trade_tags'], str):
            try:
                import json
                record['trade_tags'] = json.loads(record['trade_tags'])
            except:
                record['trade_tags'] = []
        elif not record.get('trade_tags'):
            record['trade_tags'] = []
            
        # Run enrichment if requested and data not already enriched
        if enrich_data and not record.get('latitude'):
            try:
                record = enrich_record(record)
            except Exception as e:
                print(f"Enrichment failed for {record.get('permit_id', 'unknown')}: {e}")
        
        # Compute enhanced score
        record = compute_enhanced_score(record, now, lookback_days)
        records.append(record)

    # Sort by score descending
    records.sort(key=lambda r: (r['lead_score'], r.get('issue_date', '')), reverse=True)

    # Write master CSV
    master_csv = out_dir / "enriched_leads.csv"
    _write_enriched_csv(master_csv, records)

    # Write per-jurisdiction files
    buckets: Dict[str, List[Dict[str, Any]]] = {}
    for record in records:
        buckets.setdefault(record['jurisdiction'], []).append(record)

    for jur, jur_records in buckets.items():
        fname = f"{jur.lower().replace(' ', '_')}_enriched_leads.csv"
        _write_enriched_csv(per_jur_dir / fname, jur_records)

    conn.close()
    return master_csv, len(records)


def _write_enriched_csv(path: Path, records: List[Dict[str, Any]]):
    """Write enriched records to CSV with proper field ordering."""
    path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(path, "w", newline="", encoding="utf-8") as f:
        if not records:
            writer = csv.writer(f)
            writer.writerow(ENRICHED_LEAD_FIELD_ORDER)
            return

        # Ensure all fields are present with defaults
        for record in records:
            for field in ENRICHED_LEAD_FIELD_ORDER:
                if field not in record:
                    record[field] = ""
            
            # Handle list fields (trade_tags)
            if isinstance(record.get('trade_tags'), list):
                record['trade_tags'] = ','.join(record['trade_tags'])

        writer = csv.DictWriter(f, fieldnames=ENRICHED_LEAD_FIELD_ORDER)
        writer.writeheader()
        writer.writerows(records)