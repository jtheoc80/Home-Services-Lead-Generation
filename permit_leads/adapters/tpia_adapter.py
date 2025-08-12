"""
Texas Public Information Act (TPIA) adapter for Houston and other municipalities.
Handles CSV processing from manually requested public records.
"""

import os
import csv
import logging
from datetime import datetime
from typing import Dict, Any, Iterable, Optional, List
from pathlib import Path

logger = logging.getLogger(__name__)


class TPIAAdapter:
    """
    Adapter for processing CSV files from Texas Public Information Act requests.
    
    Supports Houston and other TX municipalities that require manual TPIA requests
    for building permit data access.
    """
    
    def __init__(self, cfg: Dict[str, Any], session=None):
        self.cfg = cfg
        self.jurisdiction = cfg.get("jurisdiction", "unknown")
        self.session = session
        self.data_dir = Path(cfg.get("data_dir", "./data/tpia"))
        self.template_dir = Path(cfg.get("template_dir", "./templates/tpia"))
        
        # Ensure directories exist
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.template_dir.mkdir(parents=True, exist_ok=True)
    
    def generate_tpia_request_template(self) -> str:
        """
        Generate a TPIA request template for building permits.
        Returns the template text and saves it to a file.
        """
        template = f"""
TEXAS PUBLIC INFORMATION ACT REQUEST

To: {self.jurisdiction.title()} City Clerk / Records Department
Date: {datetime.now().strftime('%B %d, %Y')}
Re: Public Information Act Request for Building Permit Records

Dear Records Officer,

Pursuant to Chapter 552 of the Texas Government Code (Texas Public Information Act), 
I hereby request access to the following public information:

REQUESTED RECORDS:
All building permit records issued by the City of {self.jurisdiction.title()} for the time period 
from {datetime.now().strftime('%B %d, %Y')} backwards for 90 days, including but not limited to:

1. Permit number/identifier
2. Issue date
3. Property address
4. Work description/scope
5. Permit type/classification
6. Project valuation/estimated cost
7. Applicant/contractor name
8. Permit status
9. Application date
10. Any geographic coordinates (if available)

PREFERRED FORMAT:
Please provide the records in electronic format (CSV, Excel, or database export) 
if available, as this reduces processing costs and time.

COMMERCIAL USE DISCLOSURE:
This request is being made for commercial purposes related to lead generation 
for home services contractors.

CONTACT INFORMATION:
[Your Name]
[Your Address]
[Your Phone]
[Your Email]

I understand that you have 10 business days to respond to this request and will 
provide a written estimate of charges if costs exceed $40.

Thank you for your assistance with this request.

Sincerely,
[Your Signature]
[Your Printed Name]

---
NOTES FOR REQUESTOR:
- File this request with the appropriate city department
- Follow up if no response within 10 business days
- Save any CSV files to: {self.data_dir}
- Use filename format: houston_permits_YYYYMMDD.csv
"""
        
        # Save template to file
        template_file = self.template_dir / f"{self.jurisdiction}_tpia_template.txt"
        with open(template_file, 'w') as f:
            f.write(template)
        
        logger.info(f"TPIA request template generated: {template_file}")
        return template
    
    def list_available_csv_files(self) -> List[Path]:
        """List available CSV files for processing."""
        csv_files = list(self.data_dir.glob(f"{self.jurisdiction}_permits_*.csv"))
        return sorted(csv_files, key=lambda x: x.stat().st_mtime, reverse=True)
    
    def fetch_since(self, since: datetime, limit: int = 5000) -> Iterable[Dict[str, Any]]:
        """
        Process CSV files delivered via TPIA requests.
        
        Args:
            since: Only process records after this date
            limit: Maximum number of records to return
        """
        csv_files = self.list_available_csv_files()
        
        if not csv_files:
            logger.warning(f"No CSV files found for {self.jurisdiction}. "
                         f"Generate a TPIA request template first.")
            # Generate template if none exists
            self.generate_tpia_request_template()
            return
        
        logger.info(f"Processing {len(csv_files)} CSV files for {self.jurisdiction}")
        
        count = 0
        mappings = self.cfg.get("mappings", {})
        date_field = self.cfg.get("date_field", "issued_date")
        
        for csv_file in csv_files:
            if count >= limit:
                break
                
            logger.info(f"Processing CSV file: {csv_file}")
            
            try:
                with open(csv_file, 'r', encoding='utf-8') as f:
                    reader = csv.DictReader(f)
                    
                    for row in reader:
                        if count >= limit:
                            break
                        
                        # Apply field mappings
                        mapped_row = self._apply_mappings(row, mappings)
                        
                        # Filter by date if specified
                        if since and date_field in mapped_row:
                            try:
                                record_date = self._parse_date(mapped_row[date_field])
                                if record_date and record_date < since:
                                    continue
                            except Exception as e:
                                logger.warning(f"Could not parse date {mapped_row[date_field]}: {e}")
                                continue
                        
                        # Add metadata
                        mapped_row['_source_file'] = str(csv_file)
                        mapped_row['_processed_at'] = datetime.now().isoformat()
                        mapped_row['jurisdiction'] = self.jurisdiction
                        
                        yield mapped_row
                        count += 1
                        
            except Exception as e:
                logger.error(f"Error processing CSV file {csv_file}: {e}")
                continue
        
        logger.info(f"Processed {count} records from TPIA CSV files")
    
    def _apply_mappings(self, row: Dict[str, Any], mappings: Dict[str, str]) -> Dict[str, Any]:
        """Apply field mappings to transform CSV columns to standard format."""
        mapped = {}
        
        for target_field, source_field in mappings.items():
            if source_field in row:
                mapped[target_field] = row[source_field]
        
        # Include unmapped fields with prefix
        for key, value in row.items():
            if key not in mappings.values():
                mapped[f"_raw_{key}"] = value
        
        return mapped
    
    def _parse_date(self, date_str: str) -> Optional[datetime]:
        """Parse date string in various formats."""
        if not date_str:
            return None
        
        # Common date formats found in permit data
        formats = [
            "%Y-%m-%d",
            "%m/%d/%Y",
            "%m-%d-%Y",
            "%Y-%m-%d %H:%M:%S",
            "%m/%d/%Y %H:%M:%S",
        ]
        
        for fmt in formats:
            try:
                return datetime.strptime(str(date_str).strip(), fmt)
            except ValueError:
                continue
        
        logger.warning(f"Could not parse date: {date_str}")
        return None
    
    def get_status(self) -> Dict[str, Any]:
        """Get status of TPIA processing for this jurisdiction."""
        csv_files = self.list_available_csv_files()
        template_file = self.template_dir / f"{self.jurisdiction}_tpia_template.txt"
        
        return {
            "jurisdiction": self.jurisdiction,
            "template_exists": template_file.exists(),
            "template_path": str(template_file) if template_file.exists() else None,
            "csv_files_available": len(csv_files),
            "latest_csv_file": str(csv_files[0]) if csv_files else None,
            "data_directory": str(self.data_dir),
            "instructions": {
                "step_1": "Use generated TPIA template to request records from city",
                "step_2": f"Save received CSV files to {self.data_dir}",
                "step_3": f"Use filename format: {self.jurisdiction}_permits_YYYYMMDD.csv",
                "step_4": "Run ETL process to import the CSV data"
            }
        }