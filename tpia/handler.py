"""
Texas Public Information Act (TPIA) request handler.

This module provides functionality for generating TPIA request letters
and processing manually delivered CSV files from Texas jurisdictions.
"""

import logging
import csv
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from pathlib import Path
import shutil

logger = logging.getLogger(__name__)


class TPIAHandler:
    """Handler for TPIA requests and manual CSV processing."""
    
    def __init__(self, requests_dir: str = "tpia/requests", deliveries_dir: str = "tpia/deliveries"):
        """
        Initialize TPIA handler.
        
        Args:
            requests_dir: Directory for storing generated request letters
            deliveries_dir: Directory for processing delivered CSV files
        """
        self.requests_dir = Path(requests_dir)
        self.deliveries_dir = Path(deliveries_dir)
        
        # Ensure directories exist
        self.requests_dir.mkdir(parents=True, exist_ok=True)
        self.deliveries_dir.mkdir(parents=True, exist_ok=True)
    
    def generate_houston_request(
        self, 
        start_date: datetime, 
        end_date: datetime,
        requestor_info: Dict[str, str]
    ) -> str:
        """Generate Houston TPIA request letter."""
        
        template_path = Path("tpia/Houston_Building_Permits_TPIA_Request.txt")
        
        if not template_path.exists():
            raise FileNotFoundError(f"TPIA template not found: {template_path}")
        
        # Read template
        with open(template_path, 'r') as f:
            template = f.read()
        
        # Calculate dates
        request_date = datetime.now().strftime("%B %d, %Y")
        submission_date = datetime.now().strftime("%Y-%m-%d")
        response_deadline = (datetime.now() + timedelta(days=10)).strftime("%Y-%m-%d")
        followup_date = (datetime.now() + timedelta(days=15)).strftime("%Y-%m-%d")
        
        # Format template
        request_content = template.format(
            request_date=request_date,
            start_date=start_date.strftime("%B %d, %Y"),
            end_date=end_date.strftime("%B %d, %Y"),
            submission_date=submission_date,
            response_deadline=response_deadline,
            followup_date=followup_date,
            **requestor_info
        )
        
        # Save request file
        filename = f"Houston_TPIA_Request_{start_date.strftime('%Y%m%d')}_{end_date.strftime('%Y%m%d')}.txt"
        request_path = self.requests_dir / filename
        
        with open(request_path, 'w') as f:
            f.write(request_content)
        
        logger.info(f"Generated TPIA request: {request_path}")
        return str(request_path)
    
    def process_delivered_csv(
        self, 
        csv_path: str, 
        source_id: str = "tx-houston-tpia",
        archive: bool = True
    ) -> Dict[str, Any]:
        """
        Process a manually delivered CSV file from TPIA request.
        
        Args:
            csv_path: Path to the delivered CSV file
            source_id: Source identifier for tracking
            archive: Whether to archive the processed file
            
        Returns:
            Processing results
        """
        csv_file = Path(csv_path)
        
        if not csv_file.exists():
            raise FileNotFoundError(f"CSV file not found: {csv_path}")
        
        logger.info(f"Processing TPIA delivery: {csv_file}")
        
        try:
            # Read and validate CSV
            records = []
            with open(csv_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                
                for row_num, row in enumerate(reader, 1):
                    try:
                        # Clean and validate row
                        cleaned_row = self._clean_csv_row(row)
                        if cleaned_row:
                            cleaned_row['_source_id'] = source_id
                            cleaned_row['_row_number'] = row_num
                            records.append(cleaned_row)
                    except Exception as e:
                        logger.warning(f"Error processing row {row_num}: {e}")
                        continue
            
            # Generate processing report
            result = {
                'source_file': str(csv_file),
                'source_id': source_id,
                'total_rows': row_num if 'row_num' in locals() else 0,
                'processed_records': len(records),
                'processing_date': datetime.now().isoformat(),
                'records': records[:5] if len(records) > 5 else records,  # Sample
                'status': 'success'
            }
            
            # Save processed data
            processed_filename = f"{source_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            processed_path = self.deliveries_dir / "processed" / processed_filename
            processed_path.parent.mkdir(exist_ok=True)
            
            import json
            with open(processed_path, 'w') as f:
                json.dump({
                    'metadata': {k: v for k, v in result.items() if k != 'records'},
                    'records': records
                }, f, indent=2, default=str)
            
            result['processed_file'] = str(processed_path)
            
            # Archive original file if requested
            if archive:
                archive_path = self.deliveries_dir / "archive" / csv_file.name
                archive_path.parent.mkdir(exist_ok=True)
                shutil.move(str(csv_file), str(archive_path))
                result['archived_to'] = str(archive_path)
            
            logger.info(f"Processed {len(records)} records from TPIA delivery")
            return result
            
        except Exception as e:
            logger.error(f"Failed to process TPIA delivery: {e}")
            return {
                'source_file': str(csv_file),
                'status': 'error',
                'error': str(e),
                'processing_date': datetime.now().isoformat()
            }
    
    def _clean_csv_row(self, row: Dict[str, str]) -> Optional[Dict[str, Any]]:
        """Clean and normalize a CSV row from TPIA delivery."""
        if not row:
            return None
        
        # Skip empty rows
        if not any(value.strip() for value in row.values() if value):
            return None
        
        cleaned = {}
        
        # Normalize column names and values
        for key, value in row.items():
            if not key:
                continue
            
            # Clean column name
            clean_key = key.strip().lower().replace(' ', '_').replace('-', '_')
            
            # Clean value
            clean_value = value.strip() if value else ''
            
            # Skip empty values
            if not clean_value or clean_value.upper() in ['NULL', 'N/A', 'NA']:
                continue
            
            # Apply type conversions
            if 'date' in clean_key:
                clean_value = self._parse_date(clean_value)
            elif clean_key in ['estimated_cost', 'project_value', 'valuation']:
                clean_value = self._parse_currency(clean_value)
            elif clean_key in ['square_footage', 'sqft']:
                clean_value = self._parse_number(clean_value)
            
            cleaned[clean_key] = clean_value
        
        return cleaned if cleaned else None
    
    def _parse_date(self, value: str) -> Optional[str]:
        """Parse date string to ISO format."""
        if not value:
            return None
        
        # Common formats in TPIA deliveries
        date_formats = [
            '%m/%d/%Y',
            '%m/%d/%y', 
            '%Y-%m-%d',
            '%m-%d-%Y',
            '%B %d, %Y',
            '%b %d, %Y'
        ]
        
        for fmt in date_formats:
            try:
                parsed_date = datetime.strptime(value, fmt)
                return parsed_date.strftime('%Y-%m-%d')
            except ValueError:
                continue
        
        logger.warning(f"Could not parse date: {value}")
        return value  # Return original if parsing fails
    
    def _parse_currency(self, value: str) -> Optional[float]:
        """Parse currency string to float."""
        if not value:
            return None
        
        # Remove currency symbols and formatting
        clean_value = value.replace('$', '').replace(',', '').strip()
        
        try:
            return float(clean_value)
        except ValueError:
            logger.warning(f"Could not parse currency: {value}")
            return None
    
    def _parse_number(self, value: str) -> Optional[float]:
        """Parse numeric string to float."""
        if not value:
            return None
        
        # Remove formatting
        clean_value = value.replace(',', '').strip()
        
        try:
            return float(clean_value)
        except ValueError:
            logger.warning(f"Could not parse number: {value}")
            return None
    
    def list_pending_requests(self) -> List[Dict[str, Any]]:
        """List pending TPIA requests."""
        requests = []
        
        for request_file in self.requests_dir.glob("*.txt"):
            stat = request_file.stat()
            requests.append({
                'filename': request_file.name,
                'path': str(request_file),
                'created_date': datetime.fromtimestamp(stat.st_ctime).isoformat(),
                'size_bytes': stat.st_size
            })
        
        return sorted(requests, key=lambda x: x['created_date'], reverse=True)
    
    def list_deliveries(self) -> List[Dict[str, Any]]:
        """List processed deliveries."""
        deliveries = []
        
        processed_dir = self.deliveries_dir / "processed"
        if processed_dir.exists():
            for delivery_file in processed_dir.glob("*.json"):
                stat = delivery_file.stat()
                deliveries.append({
                    'filename': delivery_file.name,
                    'path': str(delivery_file),
                    'processed_date': datetime.fromtimestamp(stat.st_ctime).isoformat(),
                    'size_bytes': stat.st_size
                })
        
        return sorted(deliveries, key=lambda x: x['processed_date'], reverse=True)


def main():
    """CLI entry point for TPIA handling."""
    import argparse
    import json
    
    parser = argparse.ArgumentParser(description='Handle TPIA requests and deliveries')
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Generate request command
    generate_parser = subparsers.add_parser('generate-request', help='Generate TPIA request letter')
    generate_parser.add_argument('--start-date', required=True, help='Start date (YYYY-MM-DD)')
    generate_parser.add_argument('--end-date', required=True, help='End date (YYYY-MM-DD)')
    generate_parser.add_argument('--requestor-name', required=True, help='Requestor name')
    generate_parser.add_argument('--organization', required=True, help='Organization name')
    generate_parser.add_argument('--email', required=True, help='Contact email')
    generate_parser.add_argument('--phone', required=True, help='Contact phone')
    generate_parser.add_argument('--address', required=True, help='Requestor address')
    
    # Process delivery command
    process_parser = subparsers.add_parser('process-delivery', help='Process delivered CSV file')
    process_parser.add_argument('csv_file', help='Path to delivered CSV file')
    process_parser.add_argument('--source-id', default='tx-houston-tpia', help='Source identifier')
    process_parser.add_argument('--no-archive', action='store_true', help='Do not archive original file')
    
    # List commands
    subparsers.add_parser('list-requests', help='List pending TPIA requests')
    subparsers.add_parser('list-deliveries', help='List processed deliveries')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
    
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    handler = TPIAHandler()
    
    try:
        if args.command == 'generate-request':
            start_date = datetime.strptime(args.start_date, '%Y-%m-%d')
            end_date = datetime.strptime(args.end_date, '%Y-%m-%d')
            
            requestor_info = {
                'requestor_name': args.requestor_name,
                'organization_name': args.organization,
                'requestor_email': args.email,
                'requestor_phone': args.phone,
                'requestor_address': args.address,
                'requestor_title': 'Data Analyst',
                'requestor_signature': args.requestor_name
            }
            
            request_path = handler.generate_houston_request(start_date, end_date, requestor_info)
            print(f"Generated TPIA request: {request_path}")
            
        elif args.command == 'process-delivery':
            result = handler.process_delivered_csv(
                args.csv_file, 
                args.source_id, 
                archive=not args.no_archive
            )
            print(json.dumps(result, indent=2, default=str))
            
        elif args.command == 'list-requests':
            requests = handler.list_pending_requests()
            print(json.dumps(requests, indent=2))
            
        elif args.command == 'list-deliveries':
            deliveries = handler.list_deliveries()
            print(json.dumps(deliveries, indent=2))
        
        return 0
        
    except Exception as e:
        logger.error(f"Command failed: {e}")
        return 1


if __name__ == "__main__":
    exit(main())