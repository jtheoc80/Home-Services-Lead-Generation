#!/usr/bin/env python3
"""
Demo script for Harris County permits normalization.

This script demonstrates the normalize_permits_harris() function
without requiring a live database connection.
"""

from datetime import datetime
from typing import Dict, List, Any


class HarrisPermitNormalizer:
    """
    Simulates the normalize_permits_harris() SQL function behavior.
    This class provides the same logic as the SQL function for demonstration.
    """

    def __init__(self):
        self.permits_raw_harris = []
        self.leads = []

    def insert_raw_permit(self, permit_data: Dict[str, Any]):
        """Insert a raw Harris County permit."""
        permit = permit_data.copy()
        permit["id"] = len(self.permits_raw_harris) + 1
        permit["created_at"] = datetime.now()
        self.permits_raw_harris.append(permit)

    def normalize_permits_harris(self) -> Dict[str, int]:
        """
        Normalize permits from raw table to unified schema.
        Returns counts of processed, new, and updated records.
        """
        # Deduplicate by event_id, keeping latest
        event_ids = {}
        for permit in self.permits_raw_harris:
            event_id = permit.get("event_id")
            if (
                event_id not in event_ids
                or permit["created_at"] > event_ids[event_id]["created_at"]
            ):
                event_ids[event_id] = permit

        processed_count = 0
        new_count = 0
        updated_count = 0

        for event_id, raw_permit in event_ids.items():
            # Check if already exists
            existing_lead = None
            for i, lead in enumerate(self.leads):
                if lead.get("source_ref") == event_id:
                    existing_lead = i
                    break

            # Normalize data
            normalized = self._normalize_permit_data(raw_permit)

            if existing_lead is not None:
                # Update existing
                self.leads[existing_lead] = normalized
                updated_count += 1
            else:
                # Insert new
                self.leads.append(normalized)
                new_count += 1

            processed_count += 1

        return {
            "processed_count": processed_count,
            "new_count": new_count,
            "updated_count": updated_count,
        }

    def _normalize_permit_data(self, raw_permit: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize a single raw permit to unified schema."""
        # Normalize address
        address = raw_permit.get("address", "Address Not Available")
        if address:
            address = " ".join(address.split())  # Clean whitespace

        # Determine category
        permit_type = raw_permit.get("permit_type", "").lower()
        work_description = raw_permit.get("work_description", "").lower()

        if "residential" in permit_type or any(
            keyword in work_description
            for keyword in ["single family", "duplex", "residential", "house", "home"]
        ):
            category = "residential"
        elif "commercial" in permit_type or any(
            keyword in work_description
            for keyword in ["commercial", "office", "retail", "industrial"]
        ):
            category = "commercial"
        else:
            category = "other"

        # Extract trade tags
        trade_tags = []
        desc_lower = work_description

        if any(keyword in desc_lower for keyword in ["plumb", "water", "sewer"]):
            trade_tags.append("plumbing")
        if any(
            keyword in desc_lower for keyword in ["electric", "electrical", "wiring"]
        ):
            trade_tags.append("electrical")
        if any(
            keyword in desc_lower for keyword in ["hvac", "heating", "cooling", "air"]
        ):
            trade_tags.append("hvac")
        if any(keyword in desc_lower for keyword in ["roof", "roofing"]):
            trade_tags.append("roofing")
        if any(
            keyword in desc_lower
            for keyword in ["kitchen", "bathroom", "remodel", "renovation"]
        ):
            trade_tags.append("general_contractor")

        # NEW: Use normalize_trade function for primary trade classification
        try:
            from permit_leads.enrich import normalize_trade

            primary_trade = normalize_trade(raw_permit)
        except ImportError:
            # Fallback if import fails
            primary_trade = "General"

        return {
            "id": len(self.leads) + 1,
            "jurisdiction": "Harris County",
            "permit_id": raw_permit.get("permit_number"),
            "address": address,
            "description": raw_permit.get("work_description"),
            "work_class": raw_permit.get("permit_type"),
            "category": category,
            "status": raw_permit.get("permit_status"),
            "issue_date": raw_permit.get("issue_date"),
            "applicant": raw_permit.get("applicant_name")
            or raw_permit.get("contractor_name"),
            "owner": raw_permit.get("property_owner"),
            "value": raw_permit.get("valuation"),
            "is_residential": (category == "residential"),
            "latitude": raw_permit.get("latitude"),
            "longitude": raw_permit.get("longitude"),
            "trade_tags": trade_tags,
            "trade": primary_trade,  # NEW: Primary trade classification
            "source_ref": raw_permit.get("event_id"),
            "county": "Harris",
            "permit_type": raw_permit.get("permit_type"),
            "state": "TX",
            "created_at": datetime.now(),
            "updated_at": datetime.now(),
        }

    def get_leads_by_county(self, county: str) -> List[Dict[str, Any]]:
        """Get all leads for a specific county."""
        return [lead for lead in self.leads if lead.get("county") == county]

    def get_leads_by_source_ref(self, source_ref: str) -> Dict[str, Any]:
        """Get lead by source_ref."""
        for lead in self.leads:
            if lead.get("source_ref") == source_ref:
                return lead
        return None


def demo_harris_normalization():
    """Demonstrate the Harris County permit normalization process."""
    print("🏠 Harris County Permits Normalization Demo")
    print("=" * 50)

    # Create normalizer instance
    normalizer = HarrisPermitNormalizer()

    # Sample Harris County permit data
    sample_permits = [
        {
            "event_id": "HARRIS_DEMO_001",
            "permit_number": "BP2024001234",
            "address": "1234 Main St, Houston, TX 77001",
            "permit_type": "Residential Building",
            "work_description": "Single family residence - new construction with plumbing and electrical",
            "permit_status": "Issued",
            "issue_date": "2024-01-15T10:30:00-06:00",
            "applicant_name": "ABC Construction LLC",
            "property_owner": "John Smith",
            "valuation": 450000.0,
            "latitude": 29.7604,
            "longitude": -95.3698,
        },
        {
            "event_id": "HARRIS_DEMO_002",
            "permit_number": "BP2024001235",
            "address": "5678 Oak Avenue, Katy, TX 77494",
            "permit_type": "Residential Alteration",
            "work_description": "Kitchen renovation and bathroom remodel with HVAC updates",
            "permit_status": "Active",
            "issue_date": "2024-01-20T14:15:00-06:00",
            "applicant_name": "Home Improvement Plus",
            "property_owner": "Maria Garcia",
            "valuation": 85000.0,
            "latitude": 29.7858,
            "longitude": -95.8244,
        },
        {
            "event_id": "HARRIS_DEMO_003",
            "permit_number": "CP2024000456",
            "address": "9012 Commerce Blvd, Houston, TX 77002",
            "permit_type": "Commercial Building",
            "work_description": "Office building electrical system upgrade",
            "permit_status": "Under Review",
            "applicant_name": "Commercial Electric Co",
            "property_owner": "Business Park LLC",
            "valuation": 125000.0,
            "latitude": 29.7505,
            "longitude": -95.3605,
        },
    ]

    print("1. Inserting raw Harris County permit data...")
    for permit in sample_permits:
        normalizer.insert_raw_permit(permit)
        print(f"   ✅ Inserted permit {permit['event_id']}: {permit['permit_number']}")

    print(f"\nRaw permits count: {len(normalizer.permits_raw_harris)}")

    print("\n2. Running normalization process...")
    result = normalizer.normalize_permits_harris()

    print("📊 Normalization Results:")
    print(f"   Processed: {result['processed_count']}")
    print(f"   New: {result['new_count']}")
    print(f"   Updated: {result['updated_count']}")

    print("\n3. Normalized permits in leads table:")
    harris_leads = normalizer.get_leads_by_county("Harris")

    for lead in harris_leads:
        print(f"\n   📋 {lead['source_ref']}: {lead['permit_id']}")
        print(f"      Address: {lead['address']}")
        print(f"      Category: {lead['category']} | Value: ${lead['value']:,.2f}")
        print(
            f"      Primary Trade: {lead['trade']} | Trade Tags: {', '.join(lead['trade_tags']) if lead['trade_tags'] else 'None'}"
        )
        print(f"      Status: {lead['status']} | County: {lead['county']}")

    print("\n4. Testing deduplication...")
    # Insert duplicate with updated data
    duplicate_permit = sample_permits[0].copy()
    duplicate_permit["permit_status"] = "Final Approved"
    duplicate_permit["valuation"] = 475000.0

    normalizer.insert_raw_permit(duplicate_permit)
    print(f"   ✅ Inserted updated permit {duplicate_permit['event_id']}")

    result2 = normalizer.normalize_permits_harris()
    print(
        f"   📊 Second normalization - Processed: {result2['processed_count']}, New: {result2['new_count']}, Updated: {result2['updated_count']}"
    )

    # Check updated record
    updated_lead = normalizer.get_leads_by_source_ref("HARRIS_DEMO_001")
    print(
        f"   ✅ Updated permit status: {updated_lead['status']}, value: ${updated_lead['value']:,.2f}"
    )

    print("\n5. Summary:")
    total_leads = len(normalizer.leads)
    print(f"   Total normalized leads: {total_leads}")
    print(f"   Harris County leads: {len(harris_leads)}")

    # Show schema mapping
    print("\n6. Schema Mapping Demonstration:")
    if harris_leads:
        sample_lead = harris_leads[0]
        print("   Raw permit fields → Normalized lead fields:")
        print(f"   event_id → source_ref: {sample_lead['source_ref']}")
        print(f"   permit_number → permit_id: {sample_lead['permit_id']}")
        print(f"   permit_type → work_class/permit_type: {sample_lead['work_class']}")
        print(
            f"   work_description → description: {sample_lead['description'][:50]}..."
        )
        print(f"   valuation → value: {sample_lead['value']}")
        print(f"   applicant_name → applicant: {sample_lead['applicant']}")
        print(f"   (derived) → county: {sample_lead['county']}")
        print(f"   (derived) → jurisdiction: {sample_lead['jurisdiction']}")
        print("   (derived) → primary trade: <redacted>")
        print("   (derived) → trade_tags: <redacted>")

    print("\n🎉 Demo completed successfully!")
    print("\nThis demonstrates the core functionality of normalize_permits_harris():")
    print("✅ Deduplication by event_id (keeping latest)")
    print("✅ Upsert by source_ref (insert new, update existing)")
    print("✅ Unified schema mapping")
    print("✅ Trade tag extraction")
    print("✅ Category classification")


if __name__ == "__main__":
    demo_harris_normalization()
