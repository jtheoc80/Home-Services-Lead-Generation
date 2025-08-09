#!/usr/bin/env python3
"""
Demo data seeding script for LeadLedgerPro staging environment.
Creates 200 sample leads and 1 test user account for testing purposes.
"""
import os
import sys
import json
import uuid
import random
import logging
import argparse
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Any

# Add backend to Python path
backend_dir = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_dir))

try:
    import psycopg2
    from sqlalchemy import create_engine, text
    from sqlalchemy.exc import SQLAlchemyError
except ImportError:
    print("Error: Required dependencies not installed.")
    print("Run: pip install psycopg2-binary sqlalchemy")
    sys.exit(1)

from app.settings import settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Sample data templates
SAMPLE_JURISDICTIONS = [
    "City of Houston", "Harris County", "Montgomery County", 
    "Fort Bend County", "Galveston County"
]

SAMPLE_WORK_CLASSES = [
    "New Construction", "Addition", "Alteration", "Repair", 
    "Renovation", "Commercial Improvement"
]

SAMPLE_CATEGORIES = [
    "Residential Building", "Commercial Building", "Pool/Spa", 
    "Fence", "Driveway", "Electrical", "Plumbing", "HVAC"
]

SAMPLE_TRADE_TAGS = [
    ["roofing"], ["kitchen", "bath"], ["pool"], ["fence"], 
    ["windows"], ["foundation"], ["solar"], ["hvac"], 
    ["electrical"], ["plumbing"], ["kitchen"], ["bath"]
]

SAMPLE_ADDRESSES = [
    "1234 Main St", "5678 Oak Ave", "9012 Pine Rd", "3456 Elm Dr",
    "7890 Cedar Ln", "2468 Maple Way", "1357 Birch Ct", "9753 Ash Blvd",
    "8642 Willow St", "1111 Cherry Ave", "2222 Peach Dr", "3333 Apple Ln"
]

SAMPLE_CITIES = [
    "Houston", "Katy", "Sugar Land", "The Woodlands", "Pearland",
    "League City", "Friendswood", "Cypress", "Spring", "Tomball"
]

SAMPLE_OWNERS = [
    "John Smith", "Mary Johnson", "Robert Davis", "Linda Wilson",
    "Michael Brown", "Patricia Garcia", "James Martinez", "Jennifer Anderson",
    "David Taylor", "Sarah Thompson", "ABC Construction LLC", "XYZ Builders Inc"
]

SAMPLE_APPLICANTS = [
    "Smith Construction", "Johnson Builders", "Davis Contractors", 
    "Wilson Home Improvement", "Brown & Associates", "Garcia Construction Co",
    "Martinez Builders LLC", "Anderson Contracting", "Taylor Construction Group",
    "Thompson Home Services"
]


def generate_test_user() -> Dict[str, Any]:
    """Generate test user account data."""
    user_id = str(uuid.uuid4())
    
    return {
        "user_id": user_id,
        "email": "test@leadledderpro.com",
        "plan": "trial",
        "status": "trial",
        "trial_start_date": datetime.utcnow() - timedelta(days=5),
        "trial_end_date": datetime.utcnow() + timedelta(days=9),
        "created_at": datetime.utcnow() - timedelta(days=5)
    }


def generate_sample_leads(count: int = 200) -> List[Dict[str, Any]]:
    """Generate sample lead data."""
    leads = []
    
    for i in range(count):
        # Generate base permit data
        issue_date = datetime.utcnow() - timedelta(days=random.randint(1, 30))
        
        address = f"{random.randint(1000, 9999)} {random.choice(SAMPLE_ADDRESSES)}"
        city = random.choice(SAMPLE_CITIES)
        full_address = f"{address}, {city}, TX"
        
        # Generate estimated project value
        value = random.choice([
            random.randint(5000, 15000),      # 5k-15k
            random.randint(15000, 50000),     # 15k-50k  
            random.randint(50000, 200000),    # 50k+
            random.randint(1000, 5000)        # <5k
        ])
        
        # Generate enrichment data
        year_built = random.randint(1980, 2020)
        heated_sqft = random.randint(1200, 4500)
        
        # Generate scoring data
        lead_score = random.randint(45, 95)
        
        lead = {
            "jurisdiction": random.choice(SAMPLE_JURISDICTIONS),
            "permit_id": f"DEMO-{i+1:06d}",
            "address": full_address,
            "description": f"Demo {random.choice(SAMPLE_WORK_CLASSES).lower()} project",
            "work_class": random.choice(SAMPLE_WORK_CLASSES),
            "category": random.choice(SAMPLE_CATEGORIES),
            "status": random.choice(["Issued", "Under Review", "Approved", "Closed"]),
            "issue_date": issue_date.date(),
            "applicant": random.choice(SAMPLE_APPLICANTS),
            "owner": random.choice(SAMPLE_OWNERS),
            "value": value,
            "is_residential": True,
            "scraped_at": issue_date + timedelta(hours=random.randint(1, 12)),
            
            # Enriched location data
            "latitude": 29.7604 + random.uniform(-0.5, 0.5),  # Houston area
            "longitude": -95.3698 + random.uniform(-0.5, 0.5),
            
            # Enriched parcel data
            "apn": f"APN{random.randint(100000, 999999)}",
            "year_built": year_built,
            "heated_sqft": heated_sqft,
            "lot_size": random.randint(6000, 15000),
            "land_use": "Single Family Residential",
            
            # Enriched classification
            "owner_kind": "individual" if " LLC" not in lead.get("owner", "") else "company",
            "trade_tags": random.choice(SAMPLE_TRADE_TAGS),
            "budget_band": "$15-50k" if value >= 15000 else "$5-15k" if value >= 5000 else "<$5k",
            "start_by_estimate": issue_date.date() + timedelta(days=random.randint(30, 90)),
            
            # Scoring data
            "lead_score": lead_score,
            "score_recency": random.randint(15, 25),
            "score_trade_match": random.randint(18, 25),
            "score_value": random.randint(10, 20),
            "score_parcel_age": random.randint(5, 15),
            "score_inspection": random.randint(8, 15),
            "scoring_version": "1.0.0",
            
            "created_at": issue_date + timedelta(hours=random.randint(1, 12)),
            "updated_at": datetime.utcnow()
        }
        
        leads.append(lead)
    
    return leads


def insert_test_user(engine, user_data: Dict[str, Any]) -> bool:
    """Insert test user into database."""
    try:
        with engine.connect() as connection:
            trans = connection.begin()
            try:
                # Insert user subscription
                insert_sql = text("""
                    INSERT INTO user_subscriptions 
                    (user_id, plan, status, trial_start_date, trial_end_date, created_at, updated_at)
                    VALUES 
                    (:user_id, :plan, :status, :trial_start_date, :trial_end_date, :created_at, :updated_at)
                    ON CONFLICT (user_id) DO UPDATE SET
                        plan = EXCLUDED.plan,
                        status = EXCLUDED.status,
                        trial_start_date = EXCLUDED.trial_start_date,
                        trial_end_date = EXCLUDED.trial_end_date,
                        updated_at = EXCLUDED.updated_at
                """)
                
                connection.execute(insert_sql, {
                    "user_id": user_data["user_id"],
                    "plan": user_data["plan"],
                    "status": user_data["status"],
                    "trial_start_date": user_data["trial_start_date"],
                    "trial_end_date": user_data["trial_end_date"],
                    "created_at": user_data["created_at"],
                    "updated_at": datetime.utcnow()
                })
                
                trans.commit()
                logger.info(f"✓ Test user created: {user_data['email']}")
                return True
                
            except Exception as e:
                trans.rollback()
                logger.error(f"Failed to insert test user: {e}")
                return False
                
    except Exception as e:
        logger.error(f"Database error inserting test user: {e}")
        return False


def insert_sample_leads(engine, leads: List[Dict[str, Any]]) -> bool:
    """Insert sample leads into database."""
    try:
        with engine.connect() as connection:
            trans = connection.begin()
            try:
                insert_sql = text("""
                    INSERT INTO leads (
                        jurisdiction, permit_id, address, description, work_class, category, status,
                        issue_date, applicant, owner, value, is_residential, scraped_at,
                        latitude, longitude, apn, year_built, heated_sqft, lot_size, land_use,
                        owner_kind, trade_tags, budget_band, start_by_estimate,
                        lead_score, score_recency, score_trade_match, score_value, 
                        score_parcel_age, score_inspection, scoring_version,
                        created_at, updated_at
                    ) VALUES (
                        :jurisdiction, :permit_id, :address, :description, :work_class, :category, :status,
                        :issue_date, :applicant, :owner, :value, :is_residential, :scraped_at,
                        :latitude, :longitude, :apn, :year_built, :heated_sqft, :lot_size, :land_use,
                        :owner_kind, :trade_tags, :budget_band, :start_by_estimate,
                        :lead_score, :score_recency, :score_trade_match, :score_value,
                        :score_parcel_age, :score_inspection, :scoring_version,
                        :created_at, :updated_at
                    )
                    ON CONFLICT (jurisdiction, permit_id) DO NOTHING
                """)
                
                # Insert in batches
                batch_size = 50
                for i in range(0, len(leads), batch_size):
                    batch = leads[i:i + batch_size]
                    connection.execute(insert_sql, batch)
                    logger.info(f"✓ Inserted batch {i//batch_size + 1} ({len(batch)} leads)")
                
                trans.commit()
                logger.info(f"✓ Successfully inserted {len(leads)} sample leads")
                return True
                
            except Exception as e:
                trans.rollback()
                logger.error(f"Failed to insert leads: {e}")
                return False
                
    except Exception as e:
        logger.error(f"Database error inserting leads: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(description='Seed demo data for staging environment')
    parser.add_argument(
        '--database-url',
        help='Database URL (defaults to DATABASE_URL env var)'
    )
    parser.add_argument(
        '--lead-count',
        type=int,
        default=200,
        help='Number of sample leads to create (default: 200)'
    )
    parser.add_argument(
        '--skip-user',
        action='store_true',
        help='Skip creating test user account'
    )
    parser.add_argument(
        '--verbose',
        '-v',
        action='store_true',
        help='Enable verbose logging'
    )
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Determine database URL
    database_url = args.database_url or settings.database_url
    if not database_url:
        logger.error("No database URL provided. Set DATABASE_URL environment variable or use --database-url")
        return 1
    
    logger.info("Demo data seeding parameters:")
    logger.info(f"  Database URL: {database_url[:20]}...")
    logger.info(f"  Lead count: {args.lead_count}")
    logger.info(f"  Environment: {settings.app_env}")
    logger.info(f"  Skip user: {args.skip_user}")
    
    try:
        engine = create_engine(database_url)
        
        # Generate test data
        logger.info("Generating demo data...")
        
        if not args.skip_user:
            test_user = generate_test_user()
            logger.info(f"✓ Generated test user: {test_user['email']}")
        
        sample_leads = generate_sample_leads(args.lead_count)
        logger.info(f"✓ Generated {len(sample_leads)} sample leads")
        
        # Insert data
        success = True
        
        if not args.skip_user:
            logger.info("Inserting test user...")
            if not insert_test_user(engine, test_user):
                success = False
        
        logger.info(f"Inserting {len(sample_leads)} sample leads...")
        if not insert_sample_leads(engine, sample_leads):
            success = False
        
        if success:
            logger.info("🎉 Demo data seeding completed successfully!")
            if not args.skip_user:
                logger.info(f"Test user account: {test_user['email']}")
                logger.info(f"Test user ID: {test_user['user_id']}")
            return 0
        else:
            logger.error("❌ Demo data seeding failed!")
            return 1
            
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return 1


if __name__ == '__main__':
    sys.exit(main())