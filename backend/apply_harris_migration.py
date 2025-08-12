#!/usr/bin/env python3
"""
Script to apply the Harris County permits normalization migration.

This script applies the 005_harris_permits_normalization.sql migration
and provides utilities to test the normalize_permits_harris() function.
"""

import os
import sys
import psycopg2
from psycopg2.extras import RealDictCursor
import json
from pathlib import Path

# Add backend to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

def get_database_url():
    """Get database URL from environment or use default for testing."""
    return os.environ.get('DATABASE_URL', 'postgresql://postgres:password@localhost:5432/leadledger')

def apply_migration(conn, migration_file):
    """Apply a SQL migration file."""
    print(f"Applying migration: {migration_file}")
    
    with open(migration_file, 'r') as f:
        migration_sql = f.read()
    
    try:
        with conn.cursor() as cur:
            # Execute the migration
            cur.execute(migration_sql)
            conn.commit()
            print(f"✅ Migration {migration_file} applied successfully")
            return True
    except Exception as e:
        print(f"❌ Error applying migration {migration_file}: {e}")
        conn.rollback()
        return False

def create_sample_harris_data(conn):
    """Insert sample Harris County permit data for testing."""
    print("Creating sample Harris County permit data...")
    
    sample_permits = [
        {
            'event_id': 'HARRIS_DEMO_001',
            'permit_number': 'BP2024001234',
            'address': '1234 Main St, Houston, TX 77001',
            'permit_type': 'Residential Building',
            'work_description': 'Single family residence - new construction with plumbing and electrical',
            'permit_status': 'Issued',
            'issue_date': '2024-01-15T10:30:00-06:00',
            'application_date': '2024-01-10T09:00:00-06:00',
            'applicant_name': 'ABC Construction LLC',
            'property_owner': 'John Smith',
            'contractor_name': 'ABC Construction LLC',
            'valuation': 450000.0,
            'square_footage': 2800,
            'latitude': 29.7604,
            'longitude': -95.3698,
            'parcel_id': 'HARRIS_PARCEL_001',
            'district': 'District 1',
            'sub_type': 'New Construction',
            'raw_data': json.dumps({
                'original_source': 'Harris County API',
                'fetch_date': '2024-01-16',
                'additional_fields': {'inspector': 'Jane Doe'}
            })
        },
        {
            'event_id': 'HARRIS_DEMO_002',
            'permit_number': 'BP2024001235',
            'address': '5678 Oak Avenue, Katy, TX 77494',
            'permit_type': 'Residential Alteration',
            'work_description': 'Kitchen renovation and bathroom remodel with HVAC updates',
            'permit_status': 'Active',
            'issue_date': '2024-01-20T14:15:00-06:00',
            'application_date': '2024-01-18T11:30:00-06:00',
            'applicant_name': 'Home Improvement Plus',
            'property_owner': 'Maria Garcia',
            'contractor_name': 'Elite Contractors Inc',
            'valuation': 85000.0,
            'square_footage': 1200,
            'latitude': 29.7858,
            'longitude': -95.8244,
            'parcel_id': 'HARRIS_PARCEL_002',
            'district': 'District 3',
            'sub_type': 'Renovation',
            'raw_data': json.dumps({
                'original_source': 'Harris County API',
                'fetch_date': '2024-01-21',
                'additional_fields': {'zone': 'R1'}
            })
        },
        {
            'event_id': 'HARRIS_DEMO_003',
            'permit_number': 'CP2024000456',
            'address': '9012 Commerce Blvd, Houston, TX 77002',
            'permit_type': 'Commercial Building',
            'work_description': 'Office building electrical system upgrade',
            'permit_status': 'Under Review',
            'issue_date': None,
            'application_date': '2024-01-25T16:45:00-06:00',
            'applicant_name': 'Commercial Electric Co',
            'property_owner': 'Business Park LLC',
            'contractor_name': 'Commercial Electric Co',
            'valuation': 125000.0,
            'square_footage': 5000,
            'latitude': 29.7505,
            'longitude': -95.3605,
            'parcel_id': 'HARRIS_PARCEL_003',
            'district': 'District 2',
            'sub_type': 'Electrical',
            'raw_data': json.dumps({
                'original_source': 'Harris County API',
                'fetch_date': '2024-01-26',
                'additional_fields': {'building_type': 'office'}
            })
        }
    ]
    
    try:
        with conn.cursor() as cur:
            # Clear existing demo data
            cur.execute("DELETE FROM permits_raw_harris WHERE event_id LIKE 'HARRIS_DEMO_%'")
            
            # Insert sample permits
            insert_sql = """
            INSERT INTO permits_raw_harris 
            (event_id, permit_number, address, permit_type, work_description, permit_status,
             issue_date, application_date, applicant_name, property_owner, contractor_name,
             valuation, square_footage, latitude, longitude, parcel_id, district, sub_type, raw_data)
            VALUES (%(event_id)s, %(permit_number)s, %(address)s, %(permit_type)s, %(work_description)s,
                   %(permit_status)s, %(issue_date)s, %(application_date)s, %(applicant_name)s,
                   %(property_owner)s, %(contractor_name)s, %(valuation)s, %(square_footage)s,
                   %(latitude)s, %(longitude)s, %(parcel_id)s, %(district)s, %(sub_type)s, %(raw_data)s)
            """
            
            for permit in sample_permits:
                cur.execute(insert_sql, permit)
            
            conn.commit()
            print(f"✅ Inserted {len(sample_permits)} sample Harris County permits")
            return True
    except Exception as e:
        print(f"❌ Error creating sample data: {e}")
        conn.rollback()
        return False

def test_normalization_function(conn):
    """Test the normalize_permits_harris() function."""
    print("Testing normalize_permits_harris() function...")
    
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            # Check initial state
            cur.execute("SELECT COUNT(*) as count FROM permits_raw_harris WHERE event_id LIKE 'HARRIS_DEMO_%'")
            raw_count = cur.fetchone()['count']
            print(f"Found {raw_count} raw Harris County permits")
            
            cur.execute("SELECT COUNT(*) as count FROM leads WHERE source_ref LIKE 'HARRIS_DEMO_%'")
            existing_count = cur.fetchone()['count']
            print(f"Found {existing_count} existing normalized permits")
            
            # Run the normalization function
            cur.execute("SELECT * FROM normalize_permits_harris()")
            result = cur.fetchone()
            
            processed_count = result['processed_count']
            new_count = result['new_count'] 
            updated_count = result['updated_count']
            
            print("📊 Normalization Results:")
            print(f"   Processed: {processed_count}")
            print(f"   New: {new_count}")
            print(f"   Updated: {updated_count}")
            
            # Verify the results
            cur.execute("""
                SELECT jurisdiction, permit_id, address, category, status, county, permit_type, 
                       value, source_ref, trade_tags
                FROM leads 
                WHERE source_ref LIKE 'HARRIS_DEMO_%'
                ORDER BY source_ref
            """)
            
            normalized_permits = cur.fetchall()
            
            print(f"\n📋 Normalized Permits ({len(normalized_permits)}):")
            for permit in normalized_permits:
                print(f"   {permit['source_ref']}: {permit['permit_id']} - {permit['address']}")
                print(f"      Category: {permit['category']}, Value: ${permit['value']:,.2f}")
                print(f"      Trade Tags: {permit['trade_tags']}")
                print(f"      County: {permit['county']}, Type: {permit['permit_type']}")
                print()
            
            return True
    except Exception as e:
        print(f"❌ Error testing normalization function: {e}")
        return False

def show_schema_info(conn):
    """Show schema information for the new tables and columns."""
    print("Schema Information:")
    
    try:
        with conn.cursor() as cur:
            # Check if permits_raw_harris table exists
            cur.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = 'permits_raw_harris'
                )
            """)
            table_exists = cur.fetchone()[0]
            
            if table_exists:
                print("✅ permits_raw_harris table exists")
                
                # Show column info
                cur.execute("""
                    SELECT column_name, data_type, is_nullable
                    FROM information_schema.columns
                    WHERE table_name = 'permits_raw_harris'
                    ORDER BY ordinal_position
                """)
                columns = cur.fetchall()
                print("   Columns:")
                for col in columns:
                    print(f"      {col[0]} ({col[1]}) {'NULL' if col[2] == 'YES' else 'NOT NULL'}")
            else:
                print("❌ permits_raw_harris table does not exist")
            
            # Check if new columns exist in leads table
            cur.execute("""
                SELECT column_name 
                FROM information_schema.columns
                WHERE table_name = 'leads' 
                AND column_name IN ('source_ref', 'county', 'permit_type')
            """)
            new_columns = [row[0] for row in cur.fetchall()]
            
            print(f"\n✅ New columns in leads table: {new_columns}")
            
            # Check if function exists
            cur.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.routines
                    WHERE routine_name = 'normalize_permits_harris'
                    AND routine_type = 'FUNCTION'
                )
            """)
            function_exists = cur.fetchone()[0]
            
            if function_exists:
                print("✅ normalize_permits_harris() function exists")
            else:
                print("❌ normalize_permits_harris() function does not exist")
                
    except Exception as e:
        print(f"❌ Error checking schema: {e}")

def main():
    """Main function to run the migration and tests."""
    print("🏠 Harris County Permits Normalization Setup")
    print("=" * 50)
    
    # Get database connection
    try:
        db_url = get_database_url()
        print("Connecting to database...")
        conn = psycopg2.connect(db_url)
        print("✅ Database connection established")
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        print("Please ensure your database is running and DATABASE_URL is correct.")
        return
    
    try:
        # Apply the migration
        migration_file = Path(__file__).parent / "migrations" / "005_harris_permits_normalization.sql"
        if migration_file.exists():
            if not apply_migration(conn, migration_file):
                return
        else:
            print(f"❌ Migration file not found: {migration_file}")
            return
        
        # Show schema info
        print("\n" + "=" * 50)
        show_schema_info(conn)
        
        # Create sample data
        print("\n" + "=" * 50)
        if not create_sample_harris_data(conn):
            return
        
        # Test the function
        print("\n" + "=" * 50)
        if not test_normalization_function(conn):
            return
        
        print("\n" + "=" * 50)
        print("🎉 Harris County permits normalization setup completed successfully!")
        print("\nNext steps:")
        print("1. The normalize_permits_harris() function is ready to use")
        print("2. Insert real Harris County data into permits_raw_harris table")
        print("3. Run SELECT * FROM normalize_permits_harris() to normalize permits")
        print("4. The function will deduplicate by event_id and upsert by source_ref")
        
    finally:
        conn.close()

if __name__ == "__main__":
    main()