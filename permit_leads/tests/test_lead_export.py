"""
Tests for lead export functionality.
"""
import tempfile
import sqlite3
from pathlib import Path
from datetime import datetime, timezone
import pytest

# Add parent directory to path for imports
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from lead_export import export_leads, score_permit_rows


def test_score_permit_rows():
    """Test scoring logic with sample data."""
    # Create sample rows (simulating sqlite3.Row)
    class MockRow:
        def __init__(self, data):
            self.data = data
        
        def __getitem__(self, key):
            return self.data[key]
        
        def keys(self):
            return self.data.keys()
    
    def dict(row):
        return row.data
    
    # Mock sqlite3.Row behavior
    rows = [
        MockRow({
            'jurisdiction': 'City of Houston',
            'permit_id': 'BP123',
            'address': '123 Main St',
            'description': 'Kitchen remodel',
            'work_class': 'REMODEL',
            'category': 'residential',
            'status': 'Issued',
            'issue_date': '2025-08-01T10:00:00',
            'applicant': 'ABC Contractor',
            'owner': 'John Doe',
            'value': 50000.0,
            'is_residential': 1,
            'scraped_at': '2025-08-09T12:00:00+00:00'
        })
    ]
    
    scored = score_permit_rows(rows, lookback_days=14)
    
    assert len(scored) == 1
    lead = scored[0]
    
    # Check that scoring fields are added
    assert 'score_total' in lead
    assert 'score_recency' in lead
    assert 'score_residential' in lead
    assert 'score_value' in lead
    assert 'score_work_class' in lead
    assert 'scoring_version' in lead
    
    # Check scoring logic
    assert lead['score_residential'] == 20  # is_residential = 1
    assert lead['score_work_class'] == 15   # REMODEL keyword
    assert lead['score_value'] > 0          # Has value > 0
    assert lead['score_recency'] > 0        # Recent date
    assert lead['scoring_version'] == '1.0.0'


def test_export_leads_with_empty_db():
    """Test export with empty database."""
    with tempfile.TemporaryDirectory() as temp_dir:
        db_path = Path(temp_dir) / "test.db"
        out_dir = Path(temp_dir) / "leads"
        
        # Create empty database with permits table
        conn = sqlite3.connect(db_path)
        conn.execute("""
            CREATE TABLE permits (
                jurisdiction TEXT,
                permit_id TEXT,
                address TEXT,
                description TEXT,
                work_class TEXT,
                category TEXT,
                status TEXT,
                issue_date TEXT,
                applicant TEXT,
                owner TEXT,
                value REAL,
                is_residential INTEGER,
                scraped_at TEXT
            )
        """)
        conn.close()
        
        master_csv, count = export_leads(db_path, out_dir, lookback_days=14)
        
        assert count == 0
        assert master_csv.exists()
        
        # Check that CSV is created with headers only
        with open(master_csv, 'r') as f:
            content = f.read()
            lines = content.strip().split('\n')
            assert len(lines) == 1  # Only header row
            assert 'jurisdiction,permit_id' in lines[0]


def test_export_leads_with_sample_data():
    """Test export with sample permit data."""
    with tempfile.TemporaryDirectory() as temp_dir:
        db_path = Path(temp_dir) / "test.db"
        out_dir = Path(temp_dir) / "leads"
        
        # Create database with sample data
        conn = sqlite3.connect(db_path)
        conn.execute("""
            CREATE TABLE permits (
                jurisdiction TEXT,
                permit_id TEXT,
                address TEXT,
                description TEXT,
                work_class TEXT,
                category TEXT,
                status TEXT,
                issue_date TEXT,
                applicant TEXT,
                owner TEXT,
                value REAL,
                is_residential INTEGER,
                scraped_at TEXT
            )
        """)
        
        # Insert sample permit with today's date
        recent_date = datetime.now(timezone.utc).date().isoformat()  # Use date format like 2025-08-09
        scraped_at = datetime.now(timezone.utc).isoformat()
        
        conn.execute("""
            INSERT INTO permits VALUES (
                'City of Houston', 'BP123', '123 Main St', 'Kitchen remodel',
                'REMODEL', 'residential', 'Issued', ?, 'ABC Contractor',
                'John Doe', 50000.0, 1, ?
            )
        """, (recent_date, scraped_at))
        
        conn.commit()  # Ensure transaction is committed
        conn.close()
        
        master_csv, count = export_leads(db_path, out_dir, lookback_days=1)  # Use 1 day lookback
        
        assert count == 1
        assert master_csv.exists()
        
        # Check that by_jurisdiction file is created
        jur_dir = out_dir / "by_jurisdiction"
        assert jur_dir.exists()
        jur_files = list(jur_dir.glob("*.csv"))
        assert len(jur_files) == 1
        assert "city_of_houston_leads.csv" in jur_files[0].name


if __name__ == "__main__":
    test_score_permit_rows()
    test_export_leads_with_empty_db()
    test_export_leads_with_sample_data()
    print("All tests passed!")