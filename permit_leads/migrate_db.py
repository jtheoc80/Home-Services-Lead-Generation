"""
Database schema migration to support enriched permit data.

Adds columns for geocoding, parcel data, trade tags, and other enrichments.
"""
import sqlite3
from pathlib import Path


def add_enrichment_columns(db_path: Path):
    """Add enrichment columns to existing permits table."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Check if columns already exist
    cursor.execute("PRAGMA table_info(permits)")
    existing_columns = {row[1] for row in cursor.fetchall()}
    
    # Define new columns to add
    new_columns = [
        # Parcel/assessor data
        ("apn", "TEXT"),
        ("year_built", "INTEGER"),
        ("heated_sqft", "INTEGER"), 
        ("lot_size", "REAL"),
        ("land_use", "TEXT"),
        
        # Owner classification
        ("owner_kind", "TEXT"),
        
        # Trade and project data
        ("trade_tags", "TEXT"),  # JSON array stored as text
        ("budget_band", "TEXT"),
        ("start_by_estimate", "TEXT")  # ISO date string
    ]
    
    # Add missing columns
    for column_name, column_type in new_columns:
        if column_name not in existing_columns:
            try:
                cursor.execute(f"ALTER TABLE permits ADD COLUMN {column_name} {column_type}")
                print(f"Added column: {column_name}")
            except sqlite3.OperationalError as e:
                print(f"Column {column_name} may already exist: {e}")
    
    # Create indexes for new columns
    indexes = [
        ("idx_permits_year_built", "year_built"),
        ("idx_permits_owner_kind", "owner_kind"),
        ("idx_permits_budget_band", "budget_band"),
        ("idx_permits_apn", "apn")
    ]
    
    for index_name, column in indexes:
        try:
            cursor.execute(f"CREATE INDEX IF NOT EXISTS {index_name} ON permits({column})")
            print(f"Created index: {index_name}")
        except sqlite3.OperationalError as e:
            print(f"Index {index_name} creation failed: {e}")
    
    conn.commit()
    conn.close()
    print("Database migration completed successfully!")


def create_focus_areas_table(db_path: Path):
    """Create focus_areas table for storing user geographic preferences."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Create focus_areas table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS focus_areas (
            account_id TEXT PRIMARY KEY,
            mode TEXT NOT NULL,           -- 'zip' | 'council' | 'neighborhood' | 'radius'
            codes TEXT,                   -- JSON array of zip/district/neighborhood codes (nullable for radius)
            center_lat REAL,              -- for radius mode
            center_lon REAL,              -- for radius mode
            radius_miles REAL,            -- radius in miles (nullable for non-radius modes)
            created_at TEXT NOT NULL,     -- ISO timestamp
            updated_at TEXT NOT NULL      -- ISO timestamp
        )
    """)
    
    # Create index on account_id for fast lookups
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_focus_areas_account ON focus_areas(account_id)")
    
    conn.commit()
    conn.close()
    print("Focus areas table created successfully!")


def run_all_migrations(db_path: Path):
    """Run all database migrations."""
    print(f"Running migrations on database: {db_path}")
    add_enrichment_columns(db_path)
    create_focus_areas_table(db_path)


if __name__ == "__main__":
    import sys
    if len(sys.argv) != 2:
        print("Usage: python migrate_db.py <path_to_permits.db>")
        sys.exit(1)
    
    db_path = Path(sys.argv[1])
    if not db_path.exists():
        print(f"Database not found: {db_path}")
        sys.exit(1)
    
    run_all_migrations(db_path)