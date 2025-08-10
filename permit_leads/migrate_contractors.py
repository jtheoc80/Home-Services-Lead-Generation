"""
Database migration to add contractors table with trial and payment tracking.

Adds the contractors table with required columns for 7-day free trial feature:
- trial_start_date, trial_end_date 
- subscription_status (trial, active, canceled, expired)
- payment_method (stripe, btc, eth, xrp)
- crypto_wallet_address
"""
import sqlite3
from pathlib import Path


def create_contractors_table(db_path: Path):
    """Create contractors table with trial and payment tracking columns."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Check if contractors table already exists
    cursor.execute("""
        SELECT name FROM sqlite_master 
        WHERE type='table' AND name='contractors'
    """)
    
    if cursor.fetchone():
        print("Contractors table already exists.")
        conn.close()
        return
    
    # Create contractors table
    cursor.execute("""
        CREATE TABLE contractors (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            phone TEXT,
            company TEXT,
            password_hash TEXT NOT NULL,
            trial_start_date TIMESTAMPTZ,
            trial_end_date TIMESTAMPTZ,
            subscription_status TEXT DEFAULT 'trial' CHECK (subscription_status IN ('trial', 'active', 'canceled', 'expired')),
            payment_method TEXT CHECK (payment_method IN ('stripe', 'btc', 'eth', 'xrp')),
            crypto_wallet_address TEXT,
            created_at TEXT DEFAULT (datetime('now')),
            updated_at TEXT DEFAULT (datetime('now'))
        )
    """)
    
    # Create indexes for performance
    indexes = [
        ("idx_contractors_email", "email"),
        ("idx_contractors_subscription_status", "subscription_status"),
        ("idx_contractors_trial_end_date", "trial_end_date"),
        ("idx_contractors_payment_method", "payment_method")
    ]
    
    for index_name, column in indexes:
        cursor.execute(f"CREATE INDEX {index_name} ON contractors({column})")
        print(f"Created index: {index_name}")
    
    conn.commit()
    conn.close()
    print("Contractors table created successfully!")


def add_contractors_table_to_existing_db(db_path: Path):
    """Add contractors table to existing permits database."""
    if not db_path.exists():
        print(f"Database not found: {db_path}")
        return False
    
    try:
        create_contractors_table(db_path)
        return True
    except sqlite3.Error as e:
        print(f"Error creating contractors table: {e}")
        return False


if __name__ == "__main__":
    import sys
    if len(sys.argv) != 2:
        print("Usage: python migrate_contractors.py <path_to_permits.db>")
        sys.exit(1)
    
    db_path = Path(sys.argv[1])
    success = add_contractors_table_to_existing_db(db_path)
    sys.exit(0 if success else 1)