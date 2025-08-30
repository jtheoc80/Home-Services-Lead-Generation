"""
Lead Scoring V0 - Legacy Rules-Based Algorithm

This module contains the frozen v0 scoring logic extracted from the original
update_lead_scores.py implementation. This serves as the baseline scoring
algorithm that produces deterministic results.

The scoring algorithm considers:
- Recency scoring (max 25 points, 3x weight)
- Trade match scoring (max 25 points, 2x weight)
- Project value scoring (max 25 points, 2x weight)
- Property age scoring (max 15 points, 1x weight)
- Owner type scoring (max 10 points, 1x weight)

Final scores are capped at 100 points.
"""

from datetime import datetime
from typing import Dict, Any, List, Union


def score_v0(lead: Dict[str, Any]) -> Dict[str, Union[int, List[str]]]:
    """
    Calculate lead score using v0 rules-based algorithm.

    This is a pure function that takes a normalized lead payload and returns
    a score (0-100) with detailed reasons for the scoring.

    Args:
        lead: Dictionary containing lead data with keys:
            - created_at: datetime or ISO string when lead was created
            - trade_tags: list of trade categories
            - value: numeric project value
            - year_built: integer year property was built
            - owner_kind: string 'individual', 'llc', or other

    Returns:
        Dictionary with:
            - score: integer from 0-100
            - reasons: list of strings explaining score components
    """
    score = 0.0
    reasons = []

    # Recency scoring (max 25 points, 3x weight = 75 total points)
    if lead.get("created_at"):
        created_at = lead["created_at"]
        if isinstance(created_at, str):
            try:
                created_at = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
            except ValueError:
                created_at = datetime.now()

        days_old = (datetime.now().replace(tzinfo=created_at.tzinfo) - created_at).days
        recency_score = max(0, min(25, 25 - days_old))
        weighted_recency = recency_score * 3
        score += weighted_recency

        if recency_score > 20:
            reasons.append(
                f"Very recent lead (+{weighted_recency:.1f} pts: {days_old} days old)"
            )
        elif recency_score > 15:
            reasons.append(
                f"Recent lead (+{weighted_recency:.1f} pts: {days_old} days old)"
            )
        elif recency_score > 5:
            reasons.append(
                f"Moderately recent lead (+{weighted_recency:.1f} pts: {days_old} days old)"
            )
        else:
            reasons.append(
                f"Older lead (+{weighted_recency:.1f} pts: {days_old} days old)"
            )
    else:
        reasons.append("No creation date available (0 pts)")

    # Trade match scoring (max 25 points, 2x weight = 50 total points)
    trade_scores = {
        "roofing": 25,
        "kitchen": 24,
        "bath": 22,
        "pool": 20,
        "fence": 15,
        "windows": 18,
        "foundation": 22,
        "solar": 20,
        "hvac": 18,
        "electrical": 16,
        "plumbing": 16,
    }

    max_trade_score = 0
    matched_trade = None
    if lead.get("trade_tags"):
        for tag in lead["trade_tags"]:
            tag_score = trade_scores.get(tag, 0)
            if tag_score > max_trade_score:
                max_trade_score = tag_score
                matched_trade = tag

    weighted_trade = max_trade_score * 2
    score += weighted_trade

    if matched_trade:
        reasons.append(
            f"High-value trade match: {matched_trade} (+{weighted_trade:.1f} pts)"
        )
    elif lead.get("trade_tags"):
        reasons.append(
            f"Trade categories found but low-value (+{weighted_trade:.1f} pts)"
        )
    else:
        reasons.append("No trade categories identified (0 pts)")

    # Project value scoring (max 25 points, 2x weight = 50 total points)
    value_score = 0
    if lead.get("value"):
        value = float(lead["value"])
        if value >= 50000:
            value_score = 25
            value_desc = "$50k+"
        elif value >= 15000:
            value_score = 20
            value_desc = "$15k-50k"
        elif value >= 5000:
            value_score = 15
            value_desc = "$5k-15k"
        else:
            value_score = 10
            value_desc = "Under $5k"
    else:
        value_desc = "Unknown"
        value_score = 5  # Default small score for unknown values

    weighted_value = value_score * 2
    score += weighted_value
    reasons.append(f"Project value: {value_desc} (+{weighted_value:.1f} pts)")

    # Property age scoring (max 15 points, 1x weight = 15 total points)
    if lead.get("year_built"):
        try:
            age = datetime.now().year - int(lead["year_built"])
            if age >= 25:
                age_score = 15
                age_desc = "25+ years old"
            elif age >= 15:
                age_score = 12
                age_desc = "15-25 years old"
            elif age >= 10:
                age_score = 8
                age_desc = "10-15 years old"
            else:
                age_score = 5
                age_desc = "Under 10 years old"

            score += age_score
            reasons.append(f"Property age: {age_desc} (+{age_score:.1f} pts)")
        except (ValueError, TypeError):
            reasons.append("Invalid property age data (0 pts)")
    else:
        reasons.append("Property age unknown (0 pts)")

    # Owner type scoring (max 10 points, 1x weight = 10 total points)
    owner_score = 5  # default
    owner_kind = lead.get("owner_kind")

    if owner_kind:
        owner_kind_lower = owner_kind.lower()
        if owner_kind_lower == "individual":
            owner_score = 10
            owner_desc = "Individual owner"
        elif owner_kind_lower == "llc":
            owner_score = 7
            owner_desc = "LLC owner"
        else:
            owner_score = 5
            owner_desc = "Unknown/other owner type"
    else:
        owner_score = 5
        owner_desc = "Unknown/other owner type"

    score += owner_score
    reasons.append(f"{owner_desc} (+{owner_score:.1f} pts)")

    # Final score capping and rounding
    final_score = int(min(100, max(0, round(score))))

    # Add summary reason
    reasons.insert(0, f"Total score: {final_score}/100")

    return {"score": final_score, "reasons": reasons}


def validate_lead_input(lead: Dict[str, Any]) -> List[str]:
    """
    Validate lead input for scoring.

    Args:
        lead: Lead data dictionary

    Returns:
        List of validation error messages (empty if valid)
    """
    errors = []

    # Check for required fields (none are strictly required for scoring)
    # but warn about missing important fields
    warnings = []

    if not lead.get("created_at"):
        warnings.append("Missing created_at field - will impact recency scoring")

    if not lead.get("trade_tags"):
        warnings.append("Missing trade_tags field - will impact trade match scoring")

    if not lead.get("value"):
        warnings.append("Missing value field - will impact project value scoring")

    if not lead.get("year_built"):
        warnings.append("Missing year_built field - will impact property age scoring")

    if not lead.get("owner_kind"):
        warnings.append("Missing owner_kind field - will impact owner type scoring")

    # Type validations
    if lead.get("value") is not None:
        try:
            float(lead["value"])
        except (ValueError, TypeError):
            errors.append("Invalid value field - must be numeric")

    if lead.get("year_built") is not None:
        try:
            year = int(lead["year_built"])
            if year < 1800 or year > datetime.now().year + 5:
                errors.append(f"Invalid year_built: {year} - must be reasonable year")
        except (ValueError, TypeError):
            errors.append("Invalid year_built field - must be integer year")

    if lead.get("trade_tags") is not None:
        if not isinstance(lead["trade_tags"], list):
            errors.append("Invalid trade_tags field - must be list of strings")

    return errors
