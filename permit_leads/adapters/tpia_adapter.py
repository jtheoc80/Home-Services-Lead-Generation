"""
Texas Public Information Act (TPIA) adapter for Houston and other municipalities.
Handles CSV processing from manually requested public records.
"""

import csv
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Iterable, Optional, List
from pathlib import Path
from .base import BaseAdapter

logger = logging.getLogger(__name__)


class TPIAAdapter(BaseAdapter):
    """
    Adapter for processing CSV files from Texas Public Information Act requests.
    
    Supports Houston and other TX municipalities that require manual TPIA requests
    for building permit data access.
    """
    
    def __init__(self, cfg: Dict[str, Any], session=None):
        super().__init__(cfg, session)
        self.jurisdiction = cfg.get("jurisdiction", "unknown")
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

    # SourceAdapter interface methods
    def fetch(self, since_days: int) -> Iterable[bytes | str]:
        """Fetch raw CSV data from TPIA files."""
        since_date = datetime.utcnow() - timedelta(days=since_days)
        csv_files = self.list_available_csv_files()
        
        logger.info(f"Processing {len(csv_files)} TPIA CSV files for {self.jurisdiction}")
        
        for csv_file in csv_files:
            # Check if file is newer than since_date based on filename or modification time
            file_date = None
            
            # Try to extract date from filename (e.g., houston_permits_20231201.csv)
            if "_permits_" in csv_file.name:
                try:
                    date_str = csv_file.name.split("_permits_")[1].split(".")[0]
                    file_date = datetime.strptime(date_str, "%Y%m%d")
                except ValueError:
                    logger.debug(f"Could not parse date from filename '{csv_file.name}'")
            
            # Fall back to file modification time
            if not file_date:
                file_date = datetime.fromtimestamp(csv_file.stat().st_mtime)
            
            if file_date >= since_date:
                logger.info(f"Reading TPIA CSV file: {csv_file}")
                with open(csv_file, 'r', encoding='utf-8') as f:
                    yield f.read()

    def parse(self, raw: bytes | str) -> Iterable[Dict[str, Any]]:
        """Parse raw CSV data into individual records."""
        try:
            if isinstance(raw, bytes):
                raw = raw.decode('utf-8')
            
            # Parse CSV content
            csv_reader = csv.DictReader(raw.splitlines())
            
            for row in csv_reader:
                yield dict(row)
                
        except Exception as e:
            logger.error(f"Failed to parse TPIA CSV data: {e}")
            return

    def normalize(self, row: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize TPIA CSV record to standard format."""
        mappings = self.cfg.get("mappings", {})
        
        # Apply field mappings if configured
        normalized = {}
        for target_field, source_field in mappings.items():
            if source_field in row:
                normalized[target_field] = row[source_field]
        
        # Add standard fields with fallbacks for common Houston CSV formats
        normalized.update({
            "source": self.name,
            "permit_number": normalized.get("permit_number") or row.get("Permit Number") or row.get("PERMIT_NUMBER") or "",
            "issued_date": normalized.get("issued_date") or row.get("Issue Date") or row.get("ISSUED_DATE") or "",
            "address": normalized.get("address") or row.get("Address") or row.get("FULL_ADDRESS") or "",
            "description": normalized.get("description") or row.get("Description") or row.get("WORK_DESCRIPTION") or "",
            "status": normalized.get("status") or row.get("Status") or row.get("PERMIT_STATUS") or "",
            "work_class": normalized.get("work_class") or row.get("Work Class") or row.get("PERMIT_TYPE") or "",
            "category": normalized.get("category") or row.get("Category") or row.get("PERMIT_TYPE") or "",
            "applicant": normalized.get("applicant") or row.get("Applicant") or row.get("CONTRACTOR_NAME") or "",
            "value": self._parse_value(normalized.get("value") or row.get("Value") or row.get("DECLARED_VALUATION")),
            "raw_json": row,
        })
        
        return normalized

    def _parse_value(self, value_str: Any) -> Optional[float]:
        """Parse permit value from string."""
        if value_str is None:
            return None
        
        try:
            # Handle various value formats
            if isinstance(value_str, (int, float)):
                return float(value_str)
            
            value_str = str(value_str).strip()
            if not value_str:
                return None
            
            # Remove common prefixes and characters
            value_str = value_str.replace('$', '').replace(',', '').replace(' ', '')
            
            if value_str.lower() in ['n/a', 'na', 'none', 'null', '']:
                return None
            
            return float(value_str)
        except (ValueError, TypeError):
            return None