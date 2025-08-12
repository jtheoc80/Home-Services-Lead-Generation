"""
Simplified test fixtures for lead scoring with correct relative dates.
"""

from datetime import datetime, timedelta
from typing import List, Dict, Any

def days_ago(days: int) -> str:
    """Generate ISO date string for N days ago."""
    date = datetime.now() - timedelta(days=days)
    return date.strftime("%Y-%m-%dT%H:%M:%SZ")

# Simplified golden fixture with 20 representative leads
GOLDEN_LEAD_FIXTURES: List[Dict[str, Any]] = [
    # Perfect high-scoring lead
    {
        "lead_id": "lead-001",
        "created_at": days_ago(0),  # Today
        "trade_tags": ["roofing"],
        "value": 85000,
        "year_built": 1985,  # 39 years old
        "owner_kind": "individual",
        "address": "123 Oak Street, Houston, TX 77001",
        "description": "Replace roof shingles and gutters",
        "jurisdiction": "tx-harris",
        "expected_score": 100  # 75 (recency) + 50 (roofing) + 50 (high value) + 15 (old home) + 10 (individual) = 200, capped at 100
    },
    
    # High-scoring kitchen lead
    {
        "lead_id": "lead-002", 
        "created_at": days_ago(1),  # 1 day ago
        "trade_tags": ["kitchen"],
        "value": 45000,
        "year_built": 1988,
        "owner_kind": "individual",
        "address": "456 Maple Ave, Houston, TX 77002",
        "description": "Full kitchen renovation with new appliances",
        "jurisdiction": "tx-harris",
        "expected_score": 100  # 72 (recency) + 48 (kitchen) + 40 (good value) + 15 (old home) + 10 (individual) = 185, capped at 100
    },
    
    # Medium-scoring recent bath lead
    {
        "lead_id": "lead-003",
        "created_at": days_ago(2),  # 2 days ago
        "trade_tags": ["bath"],
        "value": 28000,
        "year_built": 1992,
        "owner_kind": "individual",
        "address": "789 Pine St, Houston, TX 77003",
        "description": "Master bathroom remodel",
        "jurisdiction": "tx-harris",
        "expected_score": 100  # 69 (recency) + 44 (bath) + 40 (decent value) + 12 (older home) + 10 (individual) = 175, capped at 100
    },
    
    # Lower-value recent lead
    {
        "lead_id": "lead-004",
        "created_at": days_ago(3),  # 3 days ago
        "trade_tags": ["fence"],
        "value": 4500,
        "year_built": 2010,
        "owner_kind": "individual",
        "address": "174 Dogwood Dr, Houston, TX 77013",
        "description": "Install privacy fence",
        "jurisdiction": "tx-harris",
        "expected_score": 75  # 66 (recency) + 30 (fence) + 20 (low value) + 8 (newer home) + 10 (individual) = 134
    },
    
    # LLC owner (lower owner score)
    {
        "lead_id": "lead-005",
        "created_at": days_ago(4),  # 4 days ago
        "trade_tags": ["pool"],
        "value": 42000,
        "year_built": 1998,
        "owner_kind": "llc",
        "address": "987 Birch Blvd, Houston, TX 77006",
        "description": "Install in-ground swimming pool",
        "jurisdiction": "tx-harris", 
        "expected_score": 100  # 63 (recency) + 40 (pool) + 40 (good value) + 12 (older home) + 7 (LLC) = 162, capped at 100
    },
    
    # Week-old lead (lower recency)
    {
        "lead_id": "lead-006",
        "created_at": days_ago(7),  # 1 week ago
        "trade_tags": ["roofing"],
        "value": 75000,
        "year_built": 1993,
        "owner_kind": "individual",
        "address": "852 Cherry Circle, Houston, TX 77011",
        "description": "Roof replacement after storm damage",
        "jurisdiction": "tx-harris",
        "expected_score": 100  # 54 (recency) + 50 (roofing) + 50 (high value) + 12 (older home) + 10 (individual) = 176, capped at 100
    },
    
    # Two-week-old lead
    {
        "lead_id": "lead-007",
        "created_at": days_ago(14),  # 2 weeks ago
        "trade_tags": ["kitchen"],
        "value": 35000,
        "year_built": 1996,
        "owner_kind": "llc",
        "address": "963 Walnut Walk, Houston, TX 77012",
        "description": "Kitchen modernization",
        "jurisdiction": "tx-harris", 
        "expected_score": 100  # 33 (recency) + 48 (kitchen) + 40 (good value) + 12 (older home) + 7 (LLC) = 140, capped at 100
    },
    
    # Month-old lead (minimal recency points)
    {
        "lead_id": "lead-008",
        "created_at": days_ago(30),  # 1 month ago
        "trade_tags": ["roofing"],
        "value": 65000,
        "year_built": 1989,
        "owner_kind": "individual",
        "address": "618 Redwood Ridge, Houston, TX 77017",
        "description": "Roof replacement", 
        "jurisdiction": "tx-harris",
        "expected_score": 85  # 0 (recency) + 50 (roofing) + 50 (high value) + 15 (old home) + 10 (individual) = 125
    },
    
    # No trade tags identified
    {
        "lead_id": "lead-009",
        "created_at": days_ago(2),  # 2 days ago
        "trade_tags": [],
        "value": 25000,
        "year_built": 1994,
        "owner_kind": "individual", 
        "address": "396 Sycamore St, Houston, TX 77015",
        "description": "General home improvements",
        "jurisdiction": "tx-harris",
        "expected_score": 67  # 69 (recency) + 0 (no trade) + 40 (decent value) + 12 (older home) + 10 (individual) = 131
    },
    
    # Missing value
    {
        "lead_id": "lead-010",
        "created_at": days_ago(3),  # 3 days ago
        "trade_tags": ["roofing"],
        "value": None,  # Missing value
        "year_built": 1992,
        "owner_kind": "individual",
        "address": "951 Peach Plaza, Houston, TX 77020",
        "description": "Roof inspection and repair",
        "jurisdiction": "tx-harris",
        "expected_score": 91  # 66 (recency) + 50 (roofing) + 10 (default value) + 12 (older home) + 10 (individual) = 148
    },
    
    # Missing year built
    {
        "lead_id": "lead-011",
        "created_at": days_ago(2),  # 2 days ago
        "trade_tags": ["kitchen"],
        "value": 28000,
        "year_built": None,  # Missing year
        "owner_kind": "individual",
        "address": "162 Persimmon Path, Houston, TX 77021",
        "description": "Kitchen cabinet replacement",
        "jurisdiction": "tx-harris",
        "expected_score": 67  # 69 (recency) + 48 (kitchen) + 40 (decent value) + 0 (no age) + 10 (individual) = 167
    },
    
    # Very new property
    {
        "lead_id": "lead-012",
        "created_at": days_ago(1),  # 1 day ago
        "trade_tags": ["kitchen"],
        "value": 40000,
        "year_built": 2020,  # 4 years old
        "owner_kind": "individual",
        "address": "507 Magnolia Manor, Houston, TX 77016",
        "description": "Kitchen upgrade in new home",
        "jurisdiction": "tx-harris",
        "expected_score": 82  # 72 (recency) + 48 (kitchen) + 40 (good value) + 5 (new home) + 10 (individual) = 175
    },
    
    # Corporate owner
    {
        "lead_id": "lead-013",
        "created_at": days_ago(1),  # 1 day ago
        "trade_tags": ["roofing"],
        "value": 65000,
        "year_built": 1989,
        "owner_kind": "corporation",
        "address": "618 Redwood Ridge, Houston, TX 77017",
        "description": "Commercial roof replacement", 
        "jurisdiction": "tx-harris",
        "expected_score": 87  # 72 (recency) + 50 (roofing) + 50 (high value) + 15 (old home) + 5 (corp) = 192
    },
    
    # Mixed trade tags (should pick best)
    {
        "lead_id": "lead-014",
        "created_at": days_ago(2),  # 2 days ago
        "trade_tags": ["electrical", "plumbing", "hvac"],
        "value": 32000,
        "year_built": 1991,
        "owner_kind": "individual",
        "address": "729 Cypress Cove, Houston, TX 77018",
        "description": "Multi-trade home renovation project",
        "jurisdiction": "tx-harris", 
        "expected_score": 76  # 69 (recency) + 36 (hvac, best of 3) + 40 (good value) + 12 (older home) + 10 (individual) = 167
    },
    
    # Unknown owner type
    {
        "lead_id": "lead-015",
        "created_at": days_ago(3),  # 3 days ago
        "trade_tags": ["bath"],
        "value": 19000,
        "year_built": 1986,
        "owner_kind": "unknown",
        "address": "840 Pecan Park, Houston, TX 77019",
        "description": "Bathroom renovation",
        "jurisdiction": "tx-harris",
        "expected_score": 71  # 66 (recency) + 44 (bath) + 30 (mid value) + 15 (old home) + 5 (unknown) = 160
    },
    
    # Minimal data
    {
        "lead_id": "lead-016",
        "created_at": days_ago(1),  # 1 day ago
        "trade_tags": [],
        "value": None,
        "year_built": None,
        "owner_kind": None,
        "address": "249 Unknown St, Houston, TX 77038",
        "description": "General permit",
        "jurisdiction": "tx-harris",
        "expected_score": 29  # 72 (recency) + 0 (no trade) + 10 (default value) + 0 (no age) + 5 (default owner) = 87
    },
    
    # Old lead with high value
    {
        "lead_id": "lead-017",
        "created_at": days_ago(60),  # 2 months ago
        "trade_tags": ["roofing"],
        "value": 95000,
        "year_built": 1985,
        "owner_kind": "individual",
        "address": "927 Sunflower St, Houston, TX 77036", 
        "description": "Complete roof replacement",
        "jurisdiction": "tx-harris",
        "expected_score": 35  # 0 (recency) + 50 (roofing) + 50 (very high value) + 15 (very old home) + 10 (individual) = 125
    },
    
    # Perfect scoring boundary test
    {
        "lead_id": "lead-018",
        "created_at": days_ago(0),  # Today
        "trade_tags": ["roofing", "kitchen", "bath"],  # Multiple high-value trades
        "value": 125000,  # Very high value
        "year_built": 1975,  # Very old home
        "owner_kind": "individual",
        "address": "471 Perfect Place, Houston, TX 77040",
        "description": "Whole house renovation after damage",
        "jurisdiction": "tx-harris",
        "expected_score": 100  # 75 (recency) + 50 (roofing, best trade) + 50 (very high value) + 15 (very old home) + 10 (individual) = 200, capped at 100
    },
    
    # Low-value fence lead
    {
        "lead_id": "lead-019",
        "created_at": days_ago(5),  # 5 days ago
        "trade_tags": ["fence"],
        "value": 3200,
        "year_built": 2015,
        "owner_kind": "llc",
        "address": "285 Hickory Hill, Houston, TX 77014",
        "description": "Fence repair and gate installation",
        "jurisdiction": "tx-harris",
        "expected_score": 48  # 60 (recency) + 30 (fence) + 20 (low value) + 5 (new home) + 7 (LLC) = 122
    },
    
    # Boundary value test ($50k exactly)
    {
        "lead_id": "lead-020",
        "created_at": days_ago(2),  # 2 days ago
        "trade_tags": ["kitchen"],
        "value": 50000,  # Exactly at $50k threshold
        "year_built": 1990,
        "owner_kind": "individual",
        "address": "915 Threshold Thruway, Houston, TX 77044",
        "description": "Kitchen renovation at budget threshold",
        "jurisdiction": "tx-harris",
        "expected_score": 100  # 69 (recency) + 48 (kitchen) + 50 (very high value, at $50k) + 15 (old home) + 10 (individual) = 192, capped at 100
    }
]


def get_lead_by_id(lead_id: str) -> Dict[str, Any]:
    """Get a specific lead fixture by ID."""
    for lead in GOLDEN_LEAD_FIXTURES:
        if lead["lead_id"] == lead_id:
            return lead.copy()
    raise ValueError(f"Lead fixture not found: {lead_id}")


def get_leads_by_score_range(min_score: int, max_score: int) -> List[Dict[str, Any]]:
    """Get all lead fixtures within a score range."""
    return [
        lead.copy() for lead in GOLDEN_LEAD_FIXTURES
        if min_score <= lead["expected_score"] <= max_score
    ]


def get_high_score_leads(threshold: int = 80) -> List[Dict[str, Any]]:
    """Get all leads with scores above threshold."""
    return get_leads_by_score_range(threshold, 100)


def get_low_score_leads(threshold: int = 50) -> List[Dict[str, Any]]:
    """Get all leads with scores below threshold.""" 
    return get_leads_by_score_range(0, threshold)