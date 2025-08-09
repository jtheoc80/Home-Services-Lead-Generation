"""
Test cases for Houston City permit scraper.
"""
import os
import pytest
from datetime import datetime, timedelta
from pathlib import Path

# Add permit_leads to path for imports
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from scrapers.houston_city import HoustonCityScraper
from models.permit import PermitRecord


class TestHoustonCityScraper:
    """Test cases for Houston City scraper functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        # Force sample data mode for tests
        os.environ['SAMPLE_DATA'] = '1'
        self.scraper = HoustonCityScraper()
        self.since_date = datetime.now() - timedelta(days=30)
    
    def teardown_method(self):
        """Clean up after tests."""
        if 'SAMPLE_DATA' in os.environ:
            del os.environ['SAMPLE_DATA']
    
    def test_scraper_initialization(self):
        """Test that scraper initializes correctly."""
        assert self.scraper.jurisdiction == "City of Houston"
        assert self.scraper.use_sample_data is True
        assert self.scraper.sample_file.exists()
    
    def test_fetch_permits_returns_list(self):
        """Test that fetch_permits returns a list of dictionaries."""
        permits = self.scraper.fetch_permits(self.since_date, limit=5)
        
        assert isinstance(permits, list)
        assert len(permits) > 0
        assert len(permits) <= 5  # Respects limit
        
        # Check that each permit is a dictionary
        for permit in permits:
            assert isinstance(permit, dict)
            assert 'Permit Number' in permit
            assert 'Issue Date' in permit
    
    def test_parse_permit_creates_valid_record(self):
        """Test that parse_permit creates valid PermitRecord objects."""
        # Get sample data
        raw_permits = self.scraper.fetch_permits(self.since_date, limit=1)
        assert len(raw_permits) > 0
        
        # Parse first permit
        raw_permit = raw_permits[0]
        permit_record = self.scraper.parse_permit(raw_permit)
        
        # Validate PermitRecord
        assert isinstance(permit_record, PermitRecord)
        assert permit_record.jurisdiction == "City of Houston"
        assert permit_record.permit_id is not None
        assert len(permit_record.permit_id) > 0
        
        # Check that required fields are populated
        assert permit_record.address is not None
        assert permit_record.description is not None
        assert permit_record.category in ['residential', 'commercial', 'other', 'unknown']
    
    def test_parse_permit_handles_residential_classification(self):
        """Test that permits are correctly classified as residential."""
        # Use sample data that should be residential
        sample_data = self.scraper.get_sample_data()
        
        for raw_permit in sample_data:
            permit_record = self.scraper.parse_permit(raw_permit)
            assert isinstance(permit_record, PermitRecord)
            
            # All sample permits should be residential
            assert permit_record.category == 'residential'
            assert permit_record.is_residential() is True
    
    def test_scrape_permits_end_to_end(self):
        """Test complete scraping workflow."""
        permits = self.scraper.scrape_permits(self.since_date, limit=3)
        
        # Should return list of PermitRecord objects
        assert isinstance(permits, list)
        assert len(permits) > 0
        assert len(permits) <= 3
        
        for permit in permits:
            assert isinstance(permit, PermitRecord)
            assert permit.jurisdiction == "City of Houston"
            assert permit.get_hash() is not None  # Should generate valid hash
    
    def test_permit_record_fields_populated(self):
        """Test that key PermitRecord fields are properly populated."""
        permits = self.scraper.scrape_permits(self.since_date, limit=1)
        assert len(permits) > 0
        
        permit = permits[0]
        
        # Check core fields are populated
        assert permit.permit_id
        assert permit.jurisdiction == "City of Houston"
        assert permit.address
        assert permit.description
        assert permit.status
        assert permit.issue_date is not None
        assert permit.applicant
        assert permit.value is not None
        assert permit.value > 0  # Should be a positive number
    
    def test_permit_hash_generation(self):
        """Test that permit records generate unique hashes."""
        permits = self.scraper.scrape_permits(self.since_date, limit=2)
        assert len(permits) >= 2
        
        hash1 = permits[0].get_hash()
        hash2 = permits[1].get_hash()
        
        # Hashes should be strings
        assert isinstance(hash1, str)
        assert isinstance(hash2, str)
        
        # Hashes should be different for different permits
        assert hash1 != hash2
        
        # Hashes should be consistent for same permit
        assert permits[0].get_hash() == hash1
    
    def test_sample_file_parsing(self):
        """Test that sample HTML file is parsed correctly."""
        # Force sample file to be used
        permits = self.scraper._fetch_sample_data(limit=10)
        
        assert isinstance(permits, list)
        assert len(permits) > 0
        
        # Check that all expected fields are present
        for permit in permits:
            required_fields = [
                'Permit Number', 'Issue Date', 'Status', 'Address',
                'Work Description', 'Permit Type', 'Applicant', 'Valuation'
            ]
            for field in required_fields:
                assert field in permit, f"Missing field {field} in permit {permit}"
    
    def test_error_handling_missing_permit_number(self):
        """Test that permits without permit numbers are skipped."""
        invalid_data = {
            'Permit Number': '',  # Empty permit number
            'Issue Date': '2025-01-15',
            'Address': '123 Test St'
        }
        
        result = self.scraper.parse_permit(invalid_data)
        assert result is None  # Should return None for invalid data
    
    def test_category_determination(self):
        """Test category determination logic."""
        # Test residential categorization
        residential_tests = [
            ('Residential Building', 'Single Family Home'),
            ('Building', 'Kitchen renovation'),
            ('Alteration', 'Bathroom remodel'),
            ('Accessory', 'Garage construction')
        ]
        
        for permit_type, description in residential_tests:
            category = self.scraper._determine_category(permit_type, description)
            assert category == 'residential', f"Expected residential for {permit_type} - {description}"
        
        # Test commercial categorization
        commercial_tests = [
            ('Commercial Building', 'Office space'),
            ('Building', 'Retail store renovation'),
            ('Industrial', 'Warehouse expansion')
        ]
        
        for permit_type, description in commercial_tests:
            category = self.scraper._determine_category(permit_type, description)
            assert category == 'commercial', f"Expected commercial for {permit_type} - {description}"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])