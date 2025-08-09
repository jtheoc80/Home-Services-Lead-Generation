"""
Storage adapter for handling PermitRecord objects - writes to CSV and SQLite.
"""
import csv
import json
import sqlite3
from pathlib import Path
from typing import List, Dict, Any, Optional
import logging
from datetime import datetime

from models.permit import PermitRecord

logger = logging.getLogger(__name__)


class Storage:
    """
    Handles writing PermitRecord objects to CSV and SQLite database.
    
    Features:
    - CSV: Append with header if new file
    - SQLite: Create table if absent, upsert by hash/permit_id+jurisdiction
    - Deduplication using record hash or (jurisdiction, permit_id)
    """
    
    def __init__(self, csv_path: Optional[Path] = None, db_path: Optional[Path] = None):
        """
        Initialize storage with optional CSV and SQLite paths.
        
        Args:
            csv_path: Path to CSV file for append operations
            db_path: Path to SQLite database file
        """
        self.csv_path = csv_path
        self.db_path = db_path
        self._csv_headers_written = False
        
        if self.db_path:
            self._init_db()
    
    def _init_db(self):
        """Initialize SQLite database with permits table."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS permits (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    hash TEXT UNIQUE,
                    jurisdiction TEXT NOT NULL,
                    permit_id TEXT,
                    address TEXT,
                    latitude REAL,
                    longitude REAL,
                    description TEXT,
                    work_class TEXT,
                    category TEXT,
                    status TEXT,
                    issue_date TEXT,
                    application_date TEXT,
                    expiration_date TEXT,
                    applicant TEXT,
                    owner TEXT,
                    value REAL,
                    source_url TEXT,
                    scraped_at TEXT,
                    extra_data JSON,
                    is_residential INTEGER,
                    created_at TEXT DEFAULT (datetime('now')),
                    updated_at TEXT DEFAULT (datetime('now')),
                    UNIQUE(jurisdiction, permit_id)
                )
            """)
            
            # Create index for common queries
            conn.execute("CREATE INDEX IF NOT EXISTS idx_permits_jurisdiction ON permits(jurisdiction)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_permits_issue_date ON permits(issue_date)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_permits_residential ON permits(is_residential)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_permits_hash ON permits(hash)")
            
            conn.commit()
    
    def save_record(self, record: PermitRecord) -> bool:
        """
        Save a single PermitRecord to both CSV and SQLite.
        
        Args:
            record: PermitRecord to save
            
        Returns:
            True if record was saved (new), False if it was a duplicate
        """
        saved_to_any = False
        
        if self.csv_path:
            saved_to_any |= self._save_to_csv(record)
        
        if self.db_path:
            saved_to_any |= self._save_to_sqlite(record)
        
        return saved_to_any
    
    def save_records(self, records: List[PermitRecord]) -> int:
        """
        Save multiple PermitRecords.
        
        Args:
            records: List of PermitRecord objects to save
            
        Returns:
            Number of new records saved (excluding duplicates)
        """
        saved_count = 0
        for record in records:
            if self.save_record(record):
                saved_count += 1
        
        logger.info(f"Saved {saved_count} new records out of {len(records)} total")
        return saved_count
    
    def _save_to_csv(self, record: PermitRecord) -> bool:
        """Save record to CSV file with append mode."""
        try:
            # Convert record to flat dict for CSV
            data = record.to_dict()
            
            # Handle datetime serialization
            for key, value in data.items():
                if isinstance(value, datetime):
                    data[key] = value.isoformat()
                elif isinstance(value, dict):
                    data[key] = json.dumps(value)
            
            file_exists = self.csv_path.exists()
            
            with open(self.csv_path, 'a', newline='', encoding='utf-8') as f:
                if not file_exists or not self._csv_headers_written:
                    # Write header if file is new
                    writer = csv.DictWriter(f, fieldnames=data.keys())
                    writer.writeheader()
                    self._csv_headers_written = True
                else:
                    writer = csv.DictWriter(f, fieldnames=data.keys())
                
                writer.writerow(data)
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to save record to CSV: {e}")
            return False
    
    def _save_to_sqlite(self, record: PermitRecord) -> bool:
        """Save record to SQLite with upsert logic."""
        try:
            record_hash = record.get_hash()
            
            with sqlite3.connect(self.db_path) as conn:
                # Check if record exists
                cursor = conn.execute(
                    "SELECT id FROM permits WHERE hash = ? OR (jurisdiction = ? AND permit_id = ?)",
                    (record_hash, record.jurisdiction, record.permit_id)
                )
                existing = cursor.fetchone()
                
                if existing:
                    # Update existing record
                    conn.execute("""
                        UPDATE permits SET 
                            address = ?, latitude = ?, longitude = ?, description = ?,
                            work_class = ?, category = ?, status = ?, issue_date = ?,
                            application_date = ?, expiration_date = ?, applicant = ?,
                            owner = ?, value = ?, source_url = ?, scraped_at = ?,
                            extra_data = ?, is_residential = ?, updated_at = datetime('now')
                        WHERE id = ?
                    """, (
                        record.address, record.latitude, record.longitude, record.description,
                        record.work_class, record.category, record.status,
                        record.issue_date.isoformat() if record.issue_date else None,
                        record.application_date.isoformat() if record.application_date else None,
                        record.expiration_date.isoformat() if record.expiration_date else None,
                        record.applicant, record.owner, record.value, record.source_url,
                        record.scraped_at.isoformat(), json.dumps(record.extra_data),
                        int(record.is_residential()), existing[0]
                    ))
                    logger.debug(f"Updated existing record: {record_hash}")
                    return False  # Not a new record
                else:
                    # Insert new record
                    conn.execute("""
                        INSERT INTO permits (
                            hash, jurisdiction, permit_id, address, latitude, longitude,
                            description, work_class, category, status, issue_date,
                            application_date, expiration_date, applicant, owner, value,
                            source_url, scraped_at, extra_data, is_residential
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        record_hash, record.jurisdiction, record.permit_id, record.address,
                        record.latitude, record.longitude, record.description, record.work_class,
                        record.category, record.status,
                        record.issue_date.isoformat() if record.issue_date else None,
                        record.application_date.isoformat() if record.application_date else None,
                        record.expiration_date.isoformat() if record.expiration_date else None,
                        record.applicant, record.owner, record.value, record.source_url,
                        record.scraped_at.isoformat(), json.dumps(record.extra_data),
                        int(record.is_residential())
                    ))
                    logger.debug(f"Inserted new record: {record_hash}")
                    return True  # New record
                
                conn.commit()
                
        except Exception as e:
            logger.error(f"Failed to save record to SQLite: {e}")
            return False
    
    def get_latest(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get latest records from SQLite database."""
        if not self.db_path or not self.db_path.exists():
            return []
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.execute("""
                    SELECT * FROM permits 
                    ORDER BY scraped_at DESC, created_at DESC 
                    LIMIT ?
                """, (limit,))
                
                return [dict(row) for row in cursor.fetchall()]
                
        except Exception as e:
            logger.error(f"Failed to get latest records: {e}")
            return []
    
    def get_stats(self) -> Dict[str, Any]:
        """Get database statistics."""
        if not self.db_path or not self.db_path.exists():
            return {}
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("""
                    SELECT 
                        COUNT(*) as total_permits,
                        COUNT(DISTINCT jurisdiction) as jurisdictions,
                        SUM(is_residential) as residential_permits,
                        MAX(scraped_at) as last_scraped,
                        MIN(issue_date) as earliest_permit,
                        MAX(issue_date) as latest_permit
                    FROM permits
                """)
                
                row = cursor.fetchone()
                return {
                    'total_permits': row[0],
                    'jurisdictions': row[1], 
                    'residential_permits': row[2],
                    'last_scraped': row[3],
                    'earliest_permit': row[4],
                    'latest_permit': row[5]
                }
                
        except Exception as e:
            logger.error(f"Failed to get stats: {e}")
            return {}