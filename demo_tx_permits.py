#!/usr/bin/env python3
"""
Texas Permits Integration Demo Script

Demonstrates how to use the new Texas permits ingest functionality
for Dallas, Austin, Arlington, and Houston.
"""

import sys
import json
from datetime import datetime, timedelta
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

def demo_dallas_socrata():
    """Demonstrate Dallas Socrata API integration."""
    print("🌟 Dallas Building Permits (Socrata API)")
    print("-" * 50)
    
    # Configuration for Dallas
    dallas_config = {
        "name": "Dallas Building Permits (Socrata)",
        "type": "socrata",
        "domain": "www.dallasopendata.com",
        "dataset_id": "e7gq-4sah",
        "updated_field": "issued_date",
        "primary_key": "permit_number",
        "mappings": {
            "permit_number": "permit_number",
            "issued_date": "issued_date",
            "address": "address",
            "work_description": "work_description",
            "permit_status": "permit_status",
            "estimated_cost": "estimated_cost",
            "contractor_name": "contractor_name"
        }
    }
    
    print(f"📊 Dataset: {dallas_config['dataset_id']}")
    print(f"🌐 API Endpoint: https://{dallas_config['domain']}/resource/{dallas_config['dataset_id']}.json")
    print(f"🔄 Incremental Field: {dallas_config['updated_field']}")
    print(f"🔑 Primary Key: {dallas_config['primary_key']}")
    print(f"📈 Rate Limit: 5 requests/second with exponential backoff")
    
    # Show example SoQL query for recent permits
    since_date = datetime.now() - timedelta(days=30)
    example_query = f"issued_date >= '{since_date.strftime('%Y-%m-%d')}'"
    print(f"\n📝 Example Query (last 30 days):")
    print(f"   $where={example_query}")
    print(f"   $limit=1000")
    print(f"   $offset=0")


def demo_austin_socrata():
    """Demonstrate Austin Socrata API integration."""
    print("\n🌟 Austin Building Permits (Socrata API)")
    print("-" * 50)
    
    austin_config = {
        "name": "Austin Building Permits (Socrata)",
        "type": "socrata", 
        "domain": "data.austintexas.gov",
        "dataset_id": "3syk-w9eu",
        "updated_field": "issued_date",
        "primary_key": "permit_number"
    }
    
    print(f"📊 Dataset: {austin_config['dataset_id']}")
    print(f"🌐 API Endpoint: https://{austin_config['domain']}/resource/{austin_config['dataset_id']}.json")
    print(f"🔄 Incremental Field: {austin_config['updated_field']}")
    print(f"🔑 Primary Key: {austin_config['primary_key']}")
    print("📈 Rate Limit: 5 requests/second with jitter")


def demo_arlington_arcgis():
    """Demonstrate Arlington ArcGIS FeatureServer integration."""
    print("\n🌟 Arlington Building Permits (ArcGIS FeatureServer)")
    print("-" * 50)
    
    arlington_config = {
        "name": "Arlington Issued Permits (ArcGIS)",
        "type": "arcgis_feature_service",
        "url": "https://gis.arlingtontx.gov/arcgis/rest/services/OpenData/Permits/FeatureServer/0/query",
        "updated_field": "IssueDate",
        "primary_key": "PermitNumber"
    }
    
    print(f"🌐 FeatureServer: {arlington_config['url']}")
    print(f"🔄 Date Field: {arlington_config['updated_field']}")
    print(f"🔑 Primary Key: {arlington_config['primary_key']}")
    print("📍 Geometry: Full PostGIS point geometry preserved")
    print("📈 Rate Limit: 5 requests/second with metadata-aware pagination")
    
    # Show example ArcGIS query
    since_date = datetime.now() - timedelta(days=30)
    example_where = f"IssueDate >= DATE '{since_date.strftime('%Y-%m-%d')}'"
    print(f"\n📝 Example Query (last 30 days):")
    print(f"   where={example_where}")
    print(f"   outFields=*")
    print(f"   returnGeometry=true")
    print(f"   f=json")


def demo_houston_tpia():
    """Demonstrate Houston TPIA integration."""
    print("\n🌟 Houston Building Permits (TPIA Request)")
    print("-" * 50)
    
    print("📋 Process:")
    print("1. Generate TPIA request template")
    print("2. Submit to Houston City Clerk")
    print("3. Receive CSV data (10 business days)")
    print("4. Process CSV through normalizer")
    
    print("\n📄 Template Generation:")
    print("   File: ./templates/tpia/houston_tpia_template.txt")
    print("   Content: Complete TPIA request letter")
    print("   Includes: Commercial use disclosure, contact info")
    
    print("\n📊 CSV Processing:")
    print("   Input: ./data/tpia/houston_permits_YYYYMMDD.csv")
    print("   Output: Normalized permits_gold records")
    print("   Fields: permit_number, issue_date, address, work_description, etc.")
    
    print("\n⚠️  Note: Houston requires manual TPIA process")
    print("   No direct API access available")


def demo_normalization():
    """Demonstrate permit data normalization."""
    print("\n🌟 Permit Data Normalization")
    print("-" * 50)
    
    print("🎯 Target Schema: permits_gold table")
    print("📊 Common Fields:")
    print("   - jurisdiction (dallas, austin, arlington, houston, harris_county)")
    print("   - issued_date (standardized timestamp)")
    print("   - work_type (residential, commercial, multi_family, infrastructure)")
    print("   - address (cleaned and standardized)")
    print("   - valuation (parsed monetary values)")
    print("   - geom (PostGIS geometry point)")
    
    print("\n🔧 Normalization Features:")
    print("   - Work type classification from descriptions")
    print("   - Value band categorization (under_1k to tier_1m_plus)")
    print("   - Coordinate validation (Texas geographic bounds)")
    print("   - Text cleaning and standardization")
    print("   - Duplicate detection via composite keys")
    
    # Example raw vs normalized data
    print("\n📋 Example Transformation:")
    
    raw_example = {
        "permit_number": "BLD2024-001234",
        "issued_date": "2024-01-15T10:30:00",
        "address": "123 MAIN ST, DALLAS, TX 75201",
        "work_description": "RESIDENTIAL ADDITION - KITCHEN REMODEL",
        "estimated_cost": "$25,000.00"
    }
    
    normalized_example = {
        "jurisdiction": "dallas",
        "source_type": "socrata",
        "permit_id": "BLD2024-001234",
        "issued_date": "2024-01-15T10:30:00",
        "work_type": "residential",
        "address": "123 Main St, Dallas, TX 75201",
        "work_description": "Residential Addition - Kitchen Remodel",
        "valuation": 25000.0,
        "project_value_band": "tier_15k_50k"
    }
    
    print("   Raw Data:")
    for key, value in raw_example.items():
        print(f"     {key}: {value}")
    
    print("   Normalized Data:")
    for key, value in normalized_example.items():
        print(f"     {key}: {value}")


def demo_analytics():
    """Demonstrate analytics capabilities."""
    print("\n🌟 Analytics and Lead Generation")
    print("-" * 50)
    
    print("📊 permits_analytics View:")
    print("   - Computed temporal columns (year, month, quarter)")
    print("   - Recency categorization (recent, current_quarter, current_year)")
    print("   - Automated work type normalization")
    print("   - Value band analysis")
    
    print("\n🎯 Example Queries:")
    
    queries = [
        {
            "title": "High-Value Residential Projects",
            "sql": """
SELECT * FROM permits_analytics 
WHERE work_type = 'residential' 
  AND valuation > 50000 
  AND recency = 'recent'
ORDER BY valuation DESC;"""
        },
        {
            "title": "Geographic Clustering",
            "sql": """
SELECT jurisdiction, 
       ST_ClusterKMeans(geom, 5) OVER() as cluster_id,
       COUNT(*) as permit_count
FROM permits_gold 
WHERE geom IS NOT NULL 
GROUP BY jurisdiction, cluster_id;"""
        },
        {
            "title": "Contractor Activity Analysis",
            "sql": """
SELECT contractor_name, 
       COUNT(*) as permit_count,
       AVG(valuation) as avg_project_value,
       MAX(issued_date) as last_permit
FROM permits_gold 
WHERE contractor_name IS NOT NULL
  AND issued_date > NOW() - INTERVAL '90 days'
GROUP BY contractor_name
ORDER BY permit_count DESC;"""
        }
    ]
    
    for i, query in enumerate(queries, 1):
        print(f"\n   {i}. {query['title']}:")
        for line in query['sql'].strip().split('\n'):
            print(f"      {line}")


def demo_usage_code():
    """Show example usage code."""
    print("\n🌟 Usage Examples")
    print("-" * 50)
    
    print("🐍 Python Code Examples:")
    
    examples = [
        {
            "title": "Fetch Dallas Permits",
            "code": """
from permit_leads.adapters.socrata_adapter import SocrataAdapter
from datetime import datetime, timedelta

config = {
    "domain": "www.dallasopendata.com",
    "dataset_id": "e7gq-4sah",
    "updated_field": "issued_date"
}

adapter = SocrataAdapter(config)
since = datetime.now() - timedelta(days=30)
permits = list(adapter.fetch_since(since, limit=1000))"""
        },
        {
            "title": "Generate Houston TPIA Template",
            "code": """
from permit_leads.adapters.tpia_adapter import TPIAAdapter

adapter = TPIAAdapter({"jurisdiction": "houston"})
template = adapter.generate_tpia_request_template()
print("Template saved to:", adapter.template_dir)"""
        },
        {
            "title": "Normalize Permit Data",
            "code": """
from permit_leads.normalizer import PermitNormalizer

normalizer = PermitNormalizer()
normalized = normalizer.normalize_batch(raw_permits, source_config)

print(f"Normalized {len(normalized)} permits")
print(f"Success rate: {normalizer.get_stats()['success_rate']:.1%}")"""
        }
    ]
    
    for i, example in enumerate(examples, 1):
        print(f"\n   {i}. {example['title']}:")
        for line in example['code'].strip().split('\n'):
            print(f"      {line}")


def main():
    """Run the complete demo."""
    print("🏠 Texas Building Permits Integration Demo")
    print("=" * 60)
    print("This demo showcases the comprehensive Texas permits ingest feature")
    print("supporting Dallas, Austin, Arlington, Harris County, and Houston.")
    print("=" * 60)
    
    demo_dallas_socrata()
    demo_austin_socrata()
    demo_arlington_arcgis()
    demo_houston_tpia()
    demo_normalization()
    demo_analytics()
    demo_usage_code()
    
    print("\n" + "=" * 60)
    print("🎉 Demo Complete!")
    print("\n📚 Next Steps:")
    print("1. Review docs/permits_tx.md for detailed documentation")
    print("2. Run SQL schema: sql/permits_gold_setup.sql")
    print("3. Configure your API tokens and database connections")
    print("4. Start with small test batches before full ETL runs")
    print("5. Monitor rate limits and API quotas")
    
    print("\n🔗 API Documentation Links:")
    print("• Dallas: https://www.dallasopendata.com/City-Services/Building-Permits/e7gq-4sah")
    print("• Austin: https://data.austintexas.gov/Building-and-Development/Issued-Construction-Permits/3syk-w9eu")
    print("• Arlington: https://gis.arlingtontx.gov/portal/home/")


if __name__ == "__main__":
    main()