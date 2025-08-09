"""
Houston City permit scraper implementation.

Scrapes building permit data from the City of Houston permit system.
Includes sample data support for testing.
"""
import os
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Any, Optional
from bs4 import BeautifulSoup
import re

from .base import BaseScraper
from ..models.permit import PermitRecord
from ..utils.normalize import safe_float, parse_date

logger = logging.getLogger(__name__)


class HoustonCityScraper(BaseScraper):
    """
    Scraper for City of Houston building permits.
    
    Features:
    - Sample data mode for testing (SAMPLE_DATA=1 environment variable)
    - Real scraping from Houston permit portal (TODO: implement live endpoint)
    - HTML table parsing with BeautifulSoup
    - Residential permit filtering
    """
    
    def __init__(self, user_agent: str = "PermitLeadBot/1.0 (+contact@example.com)",
                 delay_seconds: float = 2.0, max_retries: int = 3):
        """
        Initialize Houston City scraper.
        
        Args:
            user_agent: User-Agent string for requests
            delay_seconds: Polite delay between requests
            max_retries: Maximum number of retry attempts
        """
        super().__init__(
            jurisdiction="City of Houston",
            base_url="https://www.houstontx.gov/planning/permits/",  # TODO: Update with real endpoint
            user_agent=user_agent,
            delay_seconds=delay_seconds,
            max_retries=max_retries
        )
        
        # Check if we should use sample data
        self.use_sample_data = os.getenv('SAMPLE_DATA', '0') == '1'
        self.sample_file = Path(__file__).parent.parent / "samples" / "houston_city" / "sample_listing.html"
    
    def fetch_permits(self, since: datetime, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Fetch raw permit data from Houston City permit system.
        
        Args:
            since: Only fetch permits issued/updated since this date
            limit: Maximum number of permits to fetch
            
        Returns:
            List of raw permit data dictionaries
        """
        if self.use_sample_data or not self._is_live_endpoint_available():
            logger.info("Using sample data for Houston City permits")
            return self._fetch_sample_data(limit)
        
        # TODO: Implement live scraping once real endpoint is identified
        logger.warning("Live Houston City permit scraping not yet implemented - using sample data")
        return self._fetch_sample_data(limit)
    
    def _is_live_endpoint_available(self) -> bool:
        """
        Check if the live permit endpoint is available and accessible.
        
        Returns:
            True if live endpoint is ready for scraping
        """
        # TODO: Implement actual endpoint check
        # For now, return False to use sample data
        return False
    
    def _fetch_sample_data(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Load and parse sample permit data from HTML file.
        
        Args:
            limit: Maximum number of permits to return
            
        Returns:
            List of raw permit data dictionaries
        """
        try:
            if not self.sample_file.exists():
                logger.error(f"Sample file not found: {self.sample_file}")
                return []
            
            with open(self.sample_file, 'r', encoding='utf-8') as f:
                html_content = f.read()
            
            return self._parse_permit_table(html_content, limit)
            
        except Exception as e:
            logger.error(f"Failed to load sample data: {e}")
            return []
    
    def _fetch_live_data(self, since: datetime, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Fetch permit data from live Houston City permit portal.
        
        TODO: Implement once the actual endpoint structure is analyzed.
        This is a placeholder showing the intended structure.
        
        Args:
            since: Only fetch permits issued since this date
            limit: Maximum number of permits to fetch
            
        Returns:
            List of raw permit data dictionaries
        """
        # TODO: Real implementation would look something like:
        # 1. Build search URL with date parameters
        # 2. Handle pagination if needed
        # 3. Parse search results
        # 4. Extract permit details
        
        # Placeholder URL construction
        search_url = f"{self.base_url}search"
        params = {
            'start_date': since.strftime('%Y-%m-%d'),
            'permit_type': 'residential',  # Focus on residential permits
            'status': 'issued'
        }
        
        logger.info(f"TODO: Implement live scraping from {search_url} with params {params}")
        
        # For now, fall back to sample data
        return self._fetch_sample_data(limit)
    
    def _parse_permit_table(self, html_content: str, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Parse HTML table containing permit data.
        
        Args:
            html_content: HTML content containing permit table
            limit: Maximum number of permits to parse
            
        Returns:
            List of raw permit data dictionaries
        """
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Find the permit table
            table = soup.find('table', {'id': 'permitTable'}) or soup.find('table')
            if not table:
                logger.warning("No permit table found in HTML")
                return []
            
            # Extract headers
            header_row = table.find('thead')
            if not header_row:
                logger.warning("No table header found")
                return []
            
            headers = [th.get_text(strip=True) for th in header_row.find_all('th')]
            logger.debug(f"Found table headers: {headers}")
            
            # Extract data rows
            tbody = table.find('tbody')
            if not tbody:
                logger.warning("No table body found")
                return []
            
            rows = tbody.find_all('tr')
            permits = []
            
            for row in rows[:limit] if limit else rows:
                cells = row.find_all('td')
                if len(cells) != len(headers):
                    logger.warning(f"Row has {len(cells)} cells but expected {len(headers)}")
                    continue
                
                # Create permit data dictionary
                permit_data = {}
                for header, cell in zip(headers, cells):
                    permit_data[header] = cell.get_text(strip=True)
                
                permits.append(permit_data)
            
            logger.info(f"Parsed {len(permits)} permits from HTML table")
            return permits
            
        except Exception as e:
            logger.error(f"Failed to parse permit table: {e}")
            return []
    
    def parse_permit(self, raw_data: Dict[str, Any]) -> Optional[PermitRecord]:
        """
        Parse raw permit data into normalized PermitRecord.
        
        Args:
            raw_data: Raw permit data from fetch_permits()
            
        Returns:
            Normalized PermitRecord or None if parsing failed
        """
        try:
            # Extract and normalize fields based on Houston City format
            permit_id = raw_data.get('Permit Number', '').strip()
            if not permit_id:
                logger.warning("Missing permit number, skipping record")
                return None
            
            # Parse issue date
            issue_date_str = raw_data.get('Issue Date', '').strip()
            issue_date = parse_date(issue_date_str) if issue_date_str else None
            
            # Parse address
            address = raw_data.get('Address', '').strip()
            
            # Parse work description
            description = raw_data.get('Work Description', '').strip()
            
            # Parse permit type and category
            permit_type = raw_data.get('Permit Type', '').strip()
            category = self._determine_category(permit_type, description)
            
            # Parse status
            status = raw_data.get('Status', '').strip()
            
            # Parse applicant
            applicant = raw_data.get('Applicant', '').strip()
            
            # Parse valuation
            valuation_str = raw_data.get('Valuation', '').strip()
            value = safe_float(valuation_str.replace('$', '').replace(',', '')) if valuation_str else None
            
            # Create PermitRecord
            permit = PermitRecord(
                jurisdiction=self.jurisdiction,
                permit_id=permit_id,
                address=address,
                description=description,
                work_class=permit_type,
                category=category,
                status=status,
                issue_date=issue_date,
                applicant=applicant,
                value=value,
                source_url=self.base_url,
                extra_data=raw_data  # Store original data
            )
            
            return permit
            
        except Exception as e:
            logger.error(f"Failed to parse permit record: {e}")
            return None
    
    def _determine_category(self, permit_type: str, description: str) -> str:
        """
        Determine permit category based on type and description.
        
        Args:
            permit_type: Permit type from source
            description: Work description
            
        Returns:
            Normalized category string
        """
        if not permit_type and not description:
            return "unknown"
        
        combined_text = f"{permit_type} {description}".lower()
        
        # Check for commercial indicators first (more specific)
        commercial_keywords = [
            'commercial', 'office', 'retail', 'warehouse', 'industrial',
            'store', 'restaurant', 'hotel', 'apartment building'
        ]
        
        if any(keyword in combined_text for keyword in commercial_keywords):
            return "commercial"
        
        # Check for residential indicators
        residential_keywords = [
            'residential', 'single family', 'duplex', 'house', 'home',
            'kitchen', 'bathroom', 'bedroom', 'garage', 'pool',
            'addition', 'remodel', 'roof'
        ]
        
        if any(keyword in combined_text for keyword in residential_keywords):
            return "residential"
        
        return "other"
    
    def get_sample_data(self) -> List[Dict[str, Any]]:
        """
        Return sample permit data for testing.
        
        Returns:
            List of sample permit data dictionaries
        """
        return [
            {
                'Permit Number': 'BP2025000123',
                'Issue Date': '2025-01-15',
                'Status': 'Issued',
                'Address': '1234 Main St, Houston, TX 77001',
                'Work Description': 'Single Family Residence - New Construction',
                'Permit Type': 'Residential Building',
                'Applicant': 'ABC Construction LLC',
                'Valuation': '$450,000.00'
            },
            {
                'Permit Number': 'BP2025000124',
                'Issue Date': '2025-01-14',
                'Status': 'Issued',
                'Address': '5678 Oak Ave, Houston, TX 77002',
                'Work Description': 'Kitchen Renovation and Addition',
                'Permit Type': 'Residential Alteration',
                'Applicant': 'DEF Contractors Inc',
                'Valuation': '$85,000.00'
            }
        ]