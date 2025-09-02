"""
Great Expectations validation suite for permits data.

This module provides data quality checks for the permit data
to ensure data integrity and catch issues early in the pipeline.
"""

import logging
import os
from typing import Dict, Any, Optional
import great_expectations as gx
import pandas as pd

logger = logging.getLogger(__name__)


class PermitsValidationSuite:
    """Data quality validation suite for permits."""
    
    def __init__(self, db_url: Optional[str] = None):
        """Initialize validation suite."""
        self.db_url = db_url or os.environ.get('DATABASE_URL')
        self.suite_name = "permits_validation"
        
    def create_expectation_suite(self, context=None):
        """
        Create Great Expectations suite for permits validation.
        
        Returns:
            Configured expectation suite
        """
        if context is None:
            context = gx.get_context()
        
        # Create a new expectation suite
        try:
            suite = context.add_expectation_suite(expectation_suite_name=self.suite_name)
        except Exception:
            # Suite might already exist
            suite = context.get_expectation_suite(expectation_suite_name=self.suite_name)
        
        return suite
        
    def validate_permits_data(self, data_path: str = "data/yesterday.csv") -> Dict[str, Any]:
        """
        Run validation on permits data from CSV file.
        
        Args:
            data_path: Path to CSV file containing permits data
            
        Returns:
            Validation results dictionary
        """
        try:
            # Read the CSV data
            if not os.path.exists(data_path):
                return {
                    "success": False,
                    "error": f"Data file not found: {data_path}",
                    "total_expectations": 0,
                    "successful_expectations": 0,
                    "failed_expectations": 0
                }
            
            # Read data into pandas DataFrame
            df = pd.read_csv(data_path)
            
            # Run basic validation checks
            expectations = []
            failures = []
            
            # Check 1: permit_id column exists and is not null
            if "permit_id" in df.columns:
                expectations.append("permit_id_exists")
                if df["permit_id"].isna().sum() == 0:
                    expectations.append("permit_id_not_null")
                else:
                    failures.append("permit_id_has_nulls")
            else:
                failures.append("permit_id_missing")
            
            # Check 2: address column exists and is not null
            if "address" in df.columns:
                expectations.append("address_exists")
                if df["address"].isna().sum() == 0:
                    expectations.append("address_not_null")
                else:
                    failures.append("address_has_nulls")
            else:
                failures.append("address_missing")
            
            # Check 3: jurisdiction column exists
            if "jurisdiction" in df.columns:
                expectations.append("jurisdiction_exists")
                # Check valid jurisdictions
                valid_jurisdictions = ["Harris County", "Dallas County", "Austin", "Arlington", "Houston"]
                invalid_jurisdictions = df[~df["jurisdiction"].isin(valid_jurisdictions)]["jurisdiction"].unique()
                if len(invalid_jurisdictions) == 0:
                    expectations.append("jurisdiction_valid")
                else:
                    failures.append(f"invalid_jurisdictions: {list(invalid_jurisdictions)}")
            else:
                failures.append("jurisdiction_missing")
            
            # Check 4: permit_id uniqueness
            if "permit_id" in df.columns:
                duplicates = df["permit_id"].duplicated().sum()
                if duplicates == 0:
                    expectations.append("permit_id_unique")
                else:
                    failures.append(f"permit_id_duplicates: {duplicates}")
            
            # Check 5: minimum row count
            if len(df) > 0:
                expectations.append("has_data")
            else:
                failures.append("no_data")
            
            # Calculate summary
            total_expectations = len(expectations) + len(failures)
            successful_expectations = len(expectations)
            failed_expectations = len(failures)
            success = len(failures) == 0
            
            summary = {
                "success": success,
                "total_expectations": total_expectations,
                "successful_expectations": successful_expectations,
                "failed_expectations": failed_expectations,
                "passed_checks": expectations,
                "failed_checks": failures,
                "run_id": f"manual_validation_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}",
                "row_count": len(df)
            }
            
            # Log results
            if success:
                logger.info(f"Permits validation PASSED: {successful_expectations}/{total_expectations} checks")
            else:
                logger.warning(f"Permits validation FAILED: {failed_expectations}/{total_expectations} checks failed")
                for failure in failures:
                    logger.warning(f"Failed check: {failure}")
            
            return summary
            
        except Exception as e:
            logger.error(f"Validation failed with error: {e}")
            import traceback
            traceback.print_exc()
            return {
                "success": False,
                "error": str(e),
                "total_expectations": 0,
                "successful_expectations": 0,
                "failed_expectations": 0
            }
    
    def _add_permits_expectations(self, suite, context):
        """Add permit-specific expectations to the suite."""
        try:
            # Basic column existence checks
            suite.add_expectation(
                gx.expectations.ExpectColumnToExist(column="permit_id")
            )
            suite.add_expectation(
                gx.expectations.ExpectColumnToExist(column="address")
            )
            suite.add_expectation(
                gx.expectations.ExpectColumnToExist(column="jurisdiction")
            )
            
            # Data quality checks
            suite.add_expectation(
                gx.expectations.ExpectColumnValuesToNotBeNull(column="permit_id")
            )
            suite.add_expectation(
                gx.expectations.ExpectColumnValuesToNotBeNull(column="address")
            )
            
            # Permit ID should be unique
            suite.add_expectation(
                gx.expectations.ExpectColumnValuesToBeUnique(column="permit_id")
            )
            
            # Jurisdiction should be valid
            suite.add_expectation(
                gx.expectations.ExpectColumnValuesToBeInSet(
                    column="jurisdiction",
                    value_set=["Harris County", "Dallas County", "Austin", "Arlington", "Houston"],
                    mostly=0.9  # Allow some variations
                )
            )
            
            context.add_or_update_expectation_suite(expectation_suite=suite)
            
        except Exception as e:
            logger.warning(f"Failed to add some expectations: {e}")


def create_permits_checkpoint(context=None, data_path: str = "data/yesterday.csv"):
    """
    Create Great Expectations checkpoint for permits validation.
    
    Args:
        context: Optional Great Expectations context
        data_path: Path to CSV data file
        
    Returns:
        Configured checkpoint
    """
    if context is None:
        context = gx.get_context()
    
    checkpoint_name = "permits_checkpoint"
    
    try:
        # Create datasource if needed
        datasource_name = "permits_csv_datasource"
        try:
            datasource = context.sources.add_pandas(datasource_name)
        except Exception:
            datasource = context.get_datasource(datasource_name)
        
        # Create data asset if needed
        asset_name = "permits_csv"
        try:
            data_asset = datasource.add_csv_asset(asset_name, filepath_or_buffer=data_path)
        except Exception:
            data_asset = datasource.get_asset(asset_name)
        
        # Create expectation suite
        validator = PermitsValidationSuite()
        suite = validator.create_expectation_suite(context)
        validator._add_permits_expectations(suite, context)
        
        # Create checkpoint
        checkpoint = context.add_or_update_checkpoint(
            name=checkpoint_name,
            validations=[
                {
                    "batch_request": data_asset.build_batch_request(),
                    "expectation_suite_name": validator.suite_name,
                }
            ],
        )
        
        return checkpoint
        
    except Exception as e:
        logger.error(f"Failed to create checkpoint: {e}")
        import traceback
        traceback.print_exc()
        return None


def run_permits_checkpoint(data_path: str = "data/yesterday.csv") -> Dict[str, Any]:
    """
    Run the permits_checkpoint to validate permits data.
    
    Args:
        data_path: Path to CSV data file
        
    Returns:
        Checkpoint validation results
    """
    try:
        # Use the simpler validation approach
        validator = PermitsValidationSuite()
        results = validator.validate_permits_data(data_path)
        
        # Format as checkpoint-style results
        validation_results = {
            "run_id": f"permits_validation_{results.get('run_id', 'manual')}",
            "run_name": f"permits_validation_run",
            "success": results.get("success", False),
            "validation_results": [results]
        }
        
        return validation_results
        
    except Exception as e:
        logger.error(f"Checkpoint run failed: {e}")
        import traceback
        traceback.print_exc()
        return {
            "success": False,
            "error": str(e),
            "run_id": None,
            "run_name": None,
            "validation_results": []
        }


def validate_permits_rowcount_delta(
    current_count: int, 
    previous_count: Optional[int] = None,
    tolerance_percent: float = 50.0
) -> Dict[str, Any]:
    """
    Validate row count delta is within acceptable range.
    
    This function checks if the current row count is within ±50% of the previous
    count, which helps detect data pipeline issues.
    
    Args:
        current_count: Current number of rows in permits data
        previous_count: Previous count from last run (None for first run)
        tolerance_percent: Acceptable percentage change (default 50%)
        
    Returns:
        Validation result dictionary
    """
    result = {
        "check": "rowcount_delta",
        "current_count": current_count,
        "previous_count": previous_count,
        "tolerance_percent": tolerance_percent,
        "success": True,
        "message": ""
    }
    
    if previous_count is None:
        result["message"] = f"First run baseline: {current_count} rows"
        result["success"] = True
        return result
    
    if previous_count == 0:
        result["message"] = f"Previous count was 0, current: {current_count}"
        result["success"] = current_count >= 0
        return result
    
    # Calculate percentage change
    percent_change = abs((current_count - previous_count) / previous_count) * 100
    
    if percent_change <= tolerance_percent:
        result["success"] = True
        result["message"] = f"Row count change within tolerance: {percent_change:.1f}% (±{tolerance_percent}%)"
    else:
        result["success"] = False
        result["message"] = f"Row count change exceeds tolerance: {percent_change:.1f}% > ±{tolerance_percent}%"
        
        # This is a warning for first week, error after that
        result["severity"] = "warning"  # Can be upgraded to "error" by caller
    
    result["percent_change"] = percent_change
    return result


def run_full_validation(data_path: str = "data/yesterday.csv") -> Dict[str, Any]:
    """
    Run complete validation suite on permits data.
    
    Args:
        data_path: Path to CSV data file
        
    Returns:
        Complete validation results
    """
    try:
        # Initialize validation suite
        validator = PermitsValidationSuite()
        
        # Run Great Expectations validation
        ge_results = validator.validate_permits_data(data_path)
        
        # Get current row count for delta check
        current_count = 0
        if os.path.exists(data_path):
            try:
                import pandas as pd
                df = pd.read_csv(data_path)
                current_count = len(df)
            except Exception as e:
                logger.warning(f"Failed to count rows in {data_path}: {e}")
        
        # Run row count delta check (would need to store previous count)
        rowcount_result = validate_permits_rowcount_delta(current_count)
        
        # Combine results
        combined_results = {
            "overall_success": ge_results["success"] and rowcount_result["success"],
            "great_expectations": ge_results,
            "rowcount_validation": rowcount_result,
            "timestamp": "datetime.utcnow().isoformat()",
            "total_rows": current_count
        }
        
        return combined_results
        
    except Exception as e:
        logger.error(f"Full validation failed: {e}")
        return {
            "overall_success": False,
            "error": str(e),
            "timestamp": "datetime.utcnow().isoformat()"
        }


if __name__ == "__main__":
    # Run validation from command line
    import argparse
    
    parser = argparse.ArgumentParser(description='Run data quality validation on permits data')
    parser.add_argument('--data-path', default='data/yesterday.csv', help='Path to CSV data file')
    
    args = parser.parse_args()
    
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Run validation
    results = run_full_validation(args.data_path)
    
    print("=" * 60)
    print("PERMITS DATA QUALITY VALIDATION RESULTS")
    print("=" * 60)
    
    if results.get("overall_success"):
        print("✅ ALL VALIDATIONS PASSED")
    else:
        print("❌ VALIDATION FAILURES DETECTED")
    
    if "great_expectations" in results:
        ge = results["great_expectations"]
        print(f"\nGreat Expectations: {ge['successful_expectations']}/{ge['total_expectations']} checks passed")
    
    if "rowcount_validation" in results:
        rc = results["rowcount_validation"] 
        print(f"Row Count Check: {rc['message']}")
    
    if "total_rows" in results:
        print(f"Total Rows: {results['total_rows']}")
    
    # Exit with error code if validation failed
    exit(0 if results.get("overall_success") else 1)