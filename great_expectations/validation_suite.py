"""Great Expectations data validation suite for Texas data ingestion."""

import logging
import json
from datetime import datetime
from typing import Dict, List, Any, Optional
from pathlib import Path

logger = logging.getLogger(__name__)


class DataValidationSuite:
    """Data validation suite for Texas construction industry data."""
    
    def __init__(self, data_dir: str = "data"):
        """Initialize the validation suite."""
        self.data_dir = Path(data_dir)
        self.validation_results = []
        
    def validate_raw_data(self, file_path: str) -> Dict[str, Any]:
        """Validate raw data file."""
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
                
            if not isinstance(data, list):
                return self._create_result(file_path, False, "Data is not a list")
                
            if not data:
                return self._create_result(file_path, True, "Empty dataset", warnings=["No records to validate"])
                
            # Determine data category
            category = data[0].get("_category", "unknown")
            
            if category == "permits":
                return self._validate_permits(file_path, data)
            elif category == "violations":
                return self._validate_violations(file_path, data)
            elif category == "inspections":
                return self._validate_inspections(file_path, data)
            elif category in ["bids", "awards"]:
                return self._validate_awards(file_path, data)
            elif category == "contractors":
                return self._validate_contractors(file_path, data)
            else:
                return self._validate_generic(file_path, data)
                
        except Exception as e:
            return self._create_result(file_path, False, f"Validation error: {str(e)}")
            
    def _validate_permits(self, file_path: str, data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Validate permit data."""
        errors = []
        warnings = []
        
        # Check required fields
        required_fields = ["permit_number", "issued_date", "address"]
        for i, record in enumerate(data):
            for field in required_fields:
                if not record.get(field):
                    errors.append(f"Record {i}: Missing required field '{field}'")
                    
        # Check data types and formats
        for i, record in enumerate(data):
            # Date validation
            issued_date = record.get("issued_date")
            if issued_date:
                if not self._is_valid_date(issued_date):
                    errors.append(f"Record {i}: Invalid date format for 'issued_date': {issued_date}")
                    
            # Numeric validation
            value = record.get("value")
            if value and not self._is_valid_number(value):
                warnings.append(f"Record {i}: Invalid numeric value: {value}")
                
            # Geographic validation
            lat, lon = record.get("latitude"), record.get("longitude")
            if lat and lon:
                if not self._is_valid_texas_coordinates(lat, lon):
                    warnings.append(f"Record {i}: Coordinates outside Texas bounds: [REDACTED]")
                    
        # Check for duplicates
        permit_numbers = [r.get("permit_number") for r in data if r.get("permit_number")]
        duplicates = self._find_duplicates(permit_numbers)
        if duplicates:
            warnings.extend([f"Duplicate permit numbers found: {dup}" for dup in duplicates[:5]])
            
        # Row count validation
        if len(data) < 10:
            warnings.append(f"Low record count: {len(data)} records")
            
        return self._create_result(
            file_path, 
            len(errors) == 0,
            f"Validated {len(data)} permit records",
            errors=errors,
            warnings=warnings,
            metrics={
                "total_records": len(data),
                "records_with_coordinates": sum(1 for r in data if r.get("latitude") and r.get("longitude")),
                "records_with_value": sum(1 for r in data if r.get("value")),
                "unique_permit_numbers": len(set(permit_numbers))
            }
        )
        
    def _validate_violations(self, file_path: str, data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Validate violation data."""
        errors = []
        warnings = []
        
        # Check required fields
        required_fields = ["case_number", "created_date", "address"]
        for i, record in enumerate(data):
            for field in required_fields:
                if not record.get(field):
                    errors.append(f"Record {i}: Missing required field '{field}'")
                    
        # Check data types
        for i, record in enumerate(data):
            created_date = record.get("created_date")
            if created_date and not self._is_valid_date(created_date):
                errors.append(f"Record {i}: Invalid date format for 'created_date': {created_date}")
                
            # Geographic validation
            lat, lon = record.get("latitude"), record.get("longitude")
            if lat and lon:
                if not self._is_valid_texas_coordinates(lat, lon):
                    warnings.append(f"Record {i}: Coordinates outside Texas bounds: {lat}, {lon}")
                    
        # Check for duplicates
        case_numbers = [r.get("case_number") for r in data if r.get("case_number")]
        duplicates = self._find_duplicates(case_numbers)
        if duplicates:
            warnings.extend([f"Duplicate case numbers found: {dup}" for dup in duplicates[:5]])
            
        return self._create_result(
            file_path,
            len(errors) == 0,
            f"Validated {len(data)} violation records",
            errors=errors,
            warnings=warnings,
            metrics={
                "total_records": len(data),
                "records_with_coordinates": sum(1 for r in data if r.get("latitude") and r.get("longitude")),
                "unique_case_numbers": len(set(case_numbers))
            }
        )
        
    def _validate_inspections(self, file_path: str, data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Validate inspection data."""
        errors = []
        warnings = []
        
        # Check required fields
        required_fields = ["inspection_id", "inspection_date"]
        for i, record in enumerate(data):
            for field in required_fields:
                if not record.get(field):
                    errors.append(f"Record {i}: Missing required field '{field}'")
                    
        # Date validation
        for i, record in enumerate(data):
            inspection_date = record.get("inspection_date")
            if inspection_date and not self._is_valid_date(inspection_date):
                errors.append(f"Record {i}: Invalid date format for 'inspection_date': {inspection_date}")
                
        return self._create_result(
            file_path,
            len(errors) == 0,
            f"Validated {len(data)} inspection records",
            errors=errors,
            warnings=warnings,
            metrics={"total_records": len(data)}
        )
        
    def _validate_awards(self, file_path: str, data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Validate award/bid data."""
        errors = []
        warnings = []
        
        # Check required fields
        required_fields = ["contract_number", "award_date", "vendor_name"]
        for i, record in enumerate(data):
            for field in required_fields:
                if not record.get(field):
                    errors.append(f"Record {i}: Missing required field '{field}'")
                    
        # Validate amounts
        for i, record in enumerate(data):
            amount = record.get("amount")
            if amount and not self._is_valid_number(amount):
                warnings.append(f"Record {i}: Invalid amount: {amount}")
                
            award_date = record.get("award_date")
            if award_date and not self._is_valid_date(award_date):
                errors.append(f"Record {i}: Invalid date format for 'award_date': {award_date}")
                
        return self._create_result(
            file_path,
            len(errors) == 0,
            f"Validated {len(data)} award records",
            errors=errors,
            warnings=warnings,
            metrics={
                "total_records": len(data),
                "records_with_amount": sum(1 for r in data if r.get("amount"))
            }
        )
        
    def _validate_contractors(self, file_path: str, data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Validate contractor license data."""
        errors = []
        warnings = []
        
        # Check required fields
        required_fields = ["license_number", "business_name"]
        for i, record in enumerate(data):
            for field in required_fields:
                if not record.get(field):
                    errors.append(f"Record {i}: Missing required field '{field}'")
                    
        # Check license numbers for duplicates
        license_numbers = [r.get("license_number") for r in data if r.get("license_number")]
        duplicates = self._find_duplicates(license_numbers)
        if duplicates:
            warnings.extend([f"Duplicate license numbers found: {dup}" for dup in duplicates[:5]])
            
        # Date validation
        for i, record in enumerate(data):
            for date_field in ["issue_date", "expiration_date"]:
                date_value = record.get(date_field)
                if date_value and not self._is_valid_date(date_value):
                    warnings.append(f"Record {i}: Invalid date format for '{date_field}': {date_value}")
                    
        return self._create_result(
            file_path,
            len(errors) == 0,
            f"Validated {len(data)} contractor records",
            errors=errors,
            warnings=warnings,
            metrics={
                "total_records": len(data),
                "unique_license_numbers": len(set(license_numbers))
            }
        )
        
    def _validate_generic(self, file_path: str, data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Validate generic data records."""
        errors = []
        warnings = []
        
        # Basic structure validation
        for i, record in enumerate(data):
            if not isinstance(record, dict):
                errors.append(f"Record {i}: Not a dictionary")
                continue
                
            # Check for minimum metadata
            if not record.get("_source"):
                warnings.append(f"Record {i}: Missing source metadata")
                
            if not record.get("_category"):
                warnings.append(f"Record {i}: Missing category metadata")
                
        return self._create_result(
            file_path,
            len(errors) == 0,
            f"Validated {len(data)} generic records",
            errors=errors,
            warnings=warnings,
            metrics={"total_records": len(data)}
        )
        
    def _is_valid_date(self, date_value: Any) -> bool:
        """Check if a value is a valid date."""
        if not date_value:
            return False
            
        try:
            if isinstance(date_value, str):
                # Try common date formats
                datetime.strptime(date_value, "%Y-%m-%d")
                return True
            return False
        except ValueError:
            try:
                datetime.strptime(date_value, "%Y-%m-%dT%H:%M:%S")
                return True
            except ValueError:
                return False
                
    def _is_valid_number(self, value: Any) -> bool:
        """Check if a value is a valid number."""
        if not value:
            return False
            
        try:
            float(value)
            return True
        except (ValueError, TypeError):
            return False
            
    def _is_valid_texas_coordinates(self, lat: Any, lon: Any) -> bool:
        """Check if coordinates are within Texas bounds."""
        try:
            lat_f = float(lat)
            lon_f = float(lon)
            
            # Texas bounding box (approximate)
            return (25.0 <= lat_f <= 37.0 and -107.0 <= lon_f <= -93.0)
        except (ValueError, TypeError):
            return False
            
    def _find_duplicates(self, values: List[Any]) -> List[Any]:
        """Find duplicate values in a list."""
        seen = set()
        duplicates = set()
        
        for value in values:
            if value in seen:
                duplicates.add(value)
            else:
                seen.add(value)
                
        return list(duplicates)
        
    def _create_result(
        self, 
        file_path: str, 
        success: bool, 
        message: str,
        errors: Optional[List[str]] = None,
        warnings: Optional[List[str]] = None,
        metrics: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Create a validation result dictionary."""
        return {
            "file_path": file_path,
            "success": success,
            "message": message,
            "errors": errors or [],
            "warnings": warnings or [],
            "metrics": metrics or {},
            "validated_at": datetime.utcnow().isoformat()
        }
        
    def validate_all_raw_data(self) -> Dict[str, Any]:
        """Validate all raw data files."""
        raw_dir = self.data_dir / "raw"
        if not raw_dir.exists():
            return {"error": "Raw data directory not found"}
            
        results = []
        total_files = 0
        successful_files = 0
        
        for json_file in raw_dir.glob("*.json"):
            total_files += 1
            result = self.validate_raw_data(str(json_file))
            results.append(result)
            
            if result["success"]:
                successful_files += 1
                
            # Log results
            if result["success"]:
                logger.info(f"✓ {json_file.name}: {result['message']}")
                if result["warnings"]:
                    logger.warning(f"  Warnings: {len(result['warnings'])}")
            else:
                # Sanitize message to avoid logging sensitive data
                sanitized_message = result['message'].replace("Coordinates outside Texas bounds:", "Coordinates outside Texas bounds: [REDACTED]")
                logger.error(f"✗ {json_file.name}: {sanitized_message}")
                if result["errors"]:
                    logger.error(f"  Errors: {len(result['errors'])}")
                    
        # Save validation report
        report = {
            "summary": {
                "total_files": total_files,
                "successful_files": successful_files,
                "failed_files": total_files - successful_files,
                "success_rate": successful_files / total_files if total_files > 0 else 0
            },
            "results": results,
            "generated_at": datetime.utcnow().isoformat()
        }
        
        report_path = self.data_dir / "validation_report.json"
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2)
            
        logger.info(f"Validation report saved to {report_path}")
        
        return report
        
    def validate_normalized_data(self) -> Dict[str, Any]:
        """Validate normalized gold table data."""
        gold_dir = self.data_dir / "gold"
        if not gold_dir.exists():
            return {"error": "Gold data directory not found"}
            
        results = []
        
        for json_file in gold_dir.glob("*.json"):
            try:
                with open(json_file, 'r') as f:
                    data = json.load(f)
                    
                # Validate normalized structure
                errors = []
                warnings = []
                
                for i, record in enumerate(data):
                    # Check for required normalized fields
                    required_fields = ["id", "source", "category", "jurisdiction", "normalized_at"]
                    for field in required_fields:
                        if field not in record:
                            errors.append(f"Record {i}: Missing normalized field '{field}'")
                            
                    # Check quality score
                    quality_score = record.get("quality_score")
                    if quality_score is not None:
                        if not isinstance(quality_score, (int, float)) or not (0 <= quality_score <= 1):
                            warnings.append(f"Record {i}: Invalid quality score: {quality_score}")
                            
                result = self._create_result(
                    str(json_file),
                    len(errors) == 0,
                    f"Validated {len(data)} normalized records",
                    errors=errors,
                    warnings=warnings,
                    metrics={
                        "total_records": len(data),
                        "avg_quality_score": sum(r.get("quality_score", 0) for r in data) / len(data) if data else 0
                    }
                )
                
                results.append(result)
                
            except Exception as e:
                result = self._create_result(str(json_file), False, f"Validation error: {str(e)}")
                results.append(result)
                
        return {
            "summary": {
                "total_files": len(results),
                "successful_files": sum(1 for r in results if r["success"])
            },
            "results": results,
            "generated_at": datetime.utcnow().isoformat()
        }


def main():
    """Example usage of the data validation suite."""
    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Initialize validation suite
    validator = DataValidationSuite()
    
    # Validate all raw data
    print("Validating raw data...")
    raw_report = validator.validate_all_raw_data()
    
    print(f"\nRaw Data Validation Results:")
    print(f"  Total files: {raw_report['summary']['total_files']}")
    print(f"  Successful: {raw_report['summary']['successful_files']}")
    print(f"  Failed: {raw_report['summary']['failed_files']}")
    print(f"  Success rate: {raw_report['summary']['success_rate']:.1%}")
    
    # Validate normalized data
    print("\nValidating normalized data...")
    gold_report = validator.validate_normalized_data()
    
    print(f"\nNormalized Data Validation Results:")
    print(f"  Total files: {gold_report['summary']['total_files']}")
    print(f"  Successful: {gold_report['summary']['successful_files']}")


if __name__ == "__main__":
    main()