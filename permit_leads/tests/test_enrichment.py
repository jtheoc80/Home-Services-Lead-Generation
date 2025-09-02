"""
Test enrichment functionality.
"""

import unittest
from permit_leads.enrich import (
    normalize_address,
    derive_owner_kind,
    tag_trades,
    budget_band,
    start_by_prediction,
    enrich_record,
)


class TestEnrichment(unittest.TestCase):

    def test_normalize_address(self):
        """Test address normalization."""
        record = {"address": "  123  Main  St.  "}
        result = normalize_address(record)
        self.assertEqual(result["address"], "123 Main St.")

    def test_derive_owner_kind(self):
        """Test owner classification."""
        # LLC
        record1 = {"owner": "ABC Construction LLC"}
        result1 = derive_owner_kind(record1)
        self.assertEqual(result1["owner_kind"], "llc")

        # Individual
        record2 = {"owner": "John Smith"}
        result2 = derive_owner_kind(record2)
        self.assertEqual(result2["owner_kind"], "individual")

        # Corporation
        record3 = {"owner": "XYZ Corp"}
        result3 = derive_owner_kind(record3)
        self.assertEqual(result3["owner_kind"], "llc")

    def test_tag_trades(self):
        """Test trade tagging."""
        record1 = {"description": "Kitchen renovation", "work_class": ""}
        result1 = tag_trades(record1)
        self.assertIn("kitchen", result1["trade_tags"])

        record2 = {"description": "Bathroom and kitchen remodel", "work_class": ""}
        result2 = tag_trades(record2)
        self.assertIn("kitchen", result2["trade_tags"])
        self.assertIn("bath", result2["trade_tags"])

    def test_budget_band(self):
        """Test budget band classification."""
        self.assertEqual(budget_band(3000), "$0–5k")
        self.assertEqual(budget_band(10000), "$5–15k")
        self.assertEqual(budget_band(25000), "$15–50k")
        self.assertEqual(budget_band(75000), "$50k+")
        self.assertEqual(budget_band(0), "$0–5k")

    def test_start_by_prediction(self):
        """Test start date prediction."""
        record = {
            "issue_date": "2025-01-15T00:00:00",
            "jurisdiction": "city_of_houston",
        }
        result = start_by_prediction(record)
        self.assertEqual(result["start_by_estimate"], "2025-01-29")  # +14 days

    def test_enrich_record(self):
        """Test full record enrichment."""
        record = {
            "address": "  123  oak  ave  ",
            "description": "Kitchen renovation with new cabinets",
            "owner": "ABC LLC",
            "value": 25000,
            "issue_date": "2025-01-10T00:00:00",
            "jurisdiction": "city_of_houston",
        }

        result = enrich_record(record)

        # Check enrichments
        self.assertEqual(result["address"], "123 oak Ave")
        self.assertIn("kitchen", result["trade_tags"])
        self.assertEqual(result["owner_kind"], "llc")
        self.assertEqual(result["budget_band"], "$15–50k")
        self.assertEqual(result["start_by_estimate"], "2025-01-24")


if __name__ == "__main__":
    unittest.main()
