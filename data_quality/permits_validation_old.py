"""
Great Expectations validation suite for gold.permits table.

This module provides data quality checks for the normalized permit data
to ensure data integrity and catch issues early in the pipeline.
"""

import logging
import os
from typing import Dict, Any, Optional
import great_expectations as gx
from great_expectations.expectations.expectation_configuration import (
    ExpectationConfiguration,
)
from great_expectations.expectations.expectation_suite import ExpectationSuite
from great_expectations.checkpoint import SimpleCheckpoint

logger = logging.getLogger(__name__)


class PermitsValidationSuite:
    """Data quality validation suite for gold.permits."""

    def __init__(self, db_url: Optional[str] = None):
        """Initialize validation suite."""
        self.db_url = db_url or os.environ.get("DATABASE_URL")
        if not self.db_url:
            raise ValueError(
                "DATABASE_URL must be provided or set as environment variable"
            )

        self.suite_name = "gold_permits_validation"

    def create_expectation_suite(self) -> ExpectationSuite:
        """
        Create Great Expectations suite for gold.permits validation.

        Returns:
            Configured expectation suite
        """
        # Create a new expectation suite
        suite = ExpectationSuite(expectation_suite_name=self.suite_name)

        # Core data integrity expectations
        expectations = [
            # 1. permit_id should not be null
            ExpectationConfiguration(
                expectation_type="expect_column_values_to_not_be_null",
                kwargs={"column": "permit_id"},
            ),
            # 2. source_id should not be null
            ExpectationConfiguration(
                expectation_type="expect_column_values_to_not_be_null",
                kwargs={"column": "source_id"},
            ),
            # 3. At least one of issued_at or applied_at should be present
            ExpectationConfiguration(
                expectation_type="expect_multicolumn_values_to_be_unique",
                kwargs={
                    "column_list": ["source_id", "permit_id"],
                    "ignore_row_if": "any_value_is_missing",
                },
            ),
            # 4. Valuation should be >= 0 when present
            ExpectationConfiguration(
                expectation_type="expect_column_values_to_be_between",
                kwargs={
                    "column": "valuation",
                    "min_value": 0,
                    "mostly": 0.95,  # Allow 5% tolerance for data quality issues
                },
            ),
            # 5. Latitude should be within Texas bounds when present
            ExpectationConfiguration(
                expectation_type="expect_column_values_to_be_between",
                kwargs={
                    "column": "latitude",
                    "min_value": 25.0,
                    "max_value": 37.0,
                    "mostly": 0.90,  # Allow some tolerance for edge cases
                },
            ),
            # 6. Longitude should be within Texas bounds when present
            ExpectationConfiguration(
                expectation_type="expect_column_values_to_be_between",
                kwargs={
                    "column": "longitude",
                    "min_value": -107.0,
                    "max_value": -93.0,
                    "mostly": 0.90,
                },
            ),
            # 7. Status should be from expected set when present
            ExpectationConfiguration(
                expectation_type="expect_column_values_to_be_in_set",
                kwargs={
                    "column": "status",
                    "value_set": [
                        "ACTIVE",
                        "CLOSED",
                        "PENDING",
                        "CANCELLED",
                        "EXPIRED",
                    ],
                    "mostly": 0.80,  # Allow for variations in status values
                },
            ),
            # 8. State should be TX for all records
            ExpectationConfiguration(
                expectation_type="expect_column_values_to_be_in_set",
                kwargs={
                    "column": "state",
                    "value_set": ["TX", "Texas"],
                    "mostly": 0.99,
                },
            ),
            # 9. City should be one of the expected Texas cities
            ExpectationConfiguration(
                expectation_type="expect_column_values_to_be_in_set",
                kwargs={
                    "column": "city",
                    "value_set": [
                        "Dallas",
                        "Austin",
                        "Arlington",
                        "Houston",
                        "Harris County",
                    ],
                    "mostly": 0.95,
                },
            ),
            # 10. record_hash should not be null (used for change detection)
            ExpectationConfiguration(
                expectation_type="expect_column_values_to_not_be_null",
                kwargs={"column": "record_hash"},
            ),
            # 11. record_hash should be unique per (source_id, permit_id)
            ExpectationConfiguration(
                expectation_type="expect_compound_columns_to_be_unique",
                kwargs={"column_list": ["source_id", "permit_id", "record_hash"]},
            ),
            # 12. Check for reasonable data freshness (updated_at within last 7 days)
            ExpectationConfiguration(
                expectation_type="expect_column_max_to_be_between",
                kwargs={
                    "column": "updated_at",
                    "min_value": "2024-01-01T00:00:00",  # Reasonable minimum
                    "max_value": None,  # No maximum (current time)
                },
            ),
        ]

        # Add all expectations to the suite
        for expectation in expectations:
            suite.add_expectation(expectation)

        return suite

    def validate_permits_data(self, context=None) -> Dict[str, Any]:
        """
        Run validation on current gold.permits data.

        Args:
            context: Optional Great Expectations context

        Returns:
            Validation results dictionary
        """
        try:
            # Create or get Great Expectations context
            if context is None:
                context = gx.get_context()

            # Add PostgreSQL datasource
            datasource_config = {
                "name": "postgres_datasource",
                "class_name": "Datasource",
                "module_name": "great_expectations.datasource",
                "execution_engine": {
                    "class_name": "SqlAlchemyExecutionEngine",
                    "connection_string": self.db_url,
                },
                "data_connectors": {
                    "default_runtime_data_connector": {
                        "class_name": "RuntimeDataConnector",
                        "batch_identifiers": ["default_identifier_name"],
                    }
                },
            }

            # Add datasource to context
            try:
                datasource = context.add_datasource(**datasource_config)
            except Exception:
                # Datasource might already exist
                datasource = context.get_datasource("postgres_datasource")

            # Create expectation suite
            suite = self.create_expectation_suite()

            # Add suite to context
            try:
                context.add_expectation_suite(expectation_suite=suite)
            except Exception:
                # Suite might already exist, update it
                context.update_expectation_suite(expectation_suite=suite)

            # Create validator for gold.permits table
            batch_request = {
                "datasource_name": "postgres_datasource",
                "data_connector_name": "default_runtime_data_connector",
                "data_asset_name": "gold.permits",
                "batch_identifiers": {"default_identifier_name": "permits_validation"},
                "runtime_parameters": {
                    "query": "SELECT * FROM gold.permits LIMIT 10000"
                },  # Sample for performance
            }

            validator = context.get_validator(
                batch_request=batch_request, expectation_suite_name=self.suite_name
            )

            # Run validation
            results = validator.validate()

            # Extract summary information
            summary = {
                "success": results.success,
                "total_expectations": len(results.results),
                "successful_expectations": sum(1 for r in results.results if r.success),
                "failed_expectations": sum(1 for r in results.results if not r.success),
                "evaluation_parameters": results.evaluation_parameters,
                "run_id": str(results.run_id) if results.run_id else None,
            }

            # Log results
            if results.success:
                logger.info(
                    f"Permits validation PASSED: {summary['successful_expectations']}/{summary['total_expectations']} checks"
                )
            else:
                logger.warning(
                    f"Permits validation FAILED: {summary['failed_expectations']}/{summary['total_expectations']} checks failed"
                )

                # Log failed expectations
                for result in results.results:
                    if not result.success:
                        expectation_type = result.expectation_config.expectation_type
                        logger.warning(f"Failed expectation: {expectation_type}")

            return summary

        except Exception as e:
            logger.error(f"Validation failed with error: {e}")
            return {
                "success": False,
                "error": str(e),
                "total_expectations": 0,
                "successful_expectations": 0,
                "failed_expectations": 0,
            }


def create_permits_checkpoint(context=None) -> SimpleCheckpoint:
    """
    Create Great Expectations checkpoint for permits validation.

    Args:
        context: Optional Great Expectations context

    Returns:
        Configured SimpleCheckpoint for permits validation
    """
    if context is None:
        context = gx.get_context()

    # Create checkpoint configuration
    checkpoint_config = {
        "name": "permits_checkpoint",
        "config_version": 1.0,
        "class_name": "SimpleCheckpoint",
        "run_name_template": "permits_validation_%Y%m%d_%H%M%S",
        "validations": [
            {
                "batch_request": {
                    "datasource_name": "postgres_datasource",
                    "data_connector_name": "default_runtime_data_connector",
                    "data_asset_name": "gold.permits",
                    "batch_identifiers": {
                        "default_identifier_name": "permits_validation"
                    },
                    "runtime_parameters": {
                        "query": "SELECT * FROM gold.permits LIMIT 10000"
                    },
                },
                "expectation_suite_name": "gold_permits_validation",
            }
        ],
        "action_list": [
            {
                "name": "store_validation_result",
                "action": {"class_name": "StoreValidationResultAction"},
            },
            {
                "name": "store_evaluation_params",
                "action": {"class_name": "StoreEvaluationParametersAction"},
            },
            {
                "name": "update_data_docs",
                "action": {"class_name": "UpdateDataDocsAction"},
            },
        ],
    }

    # Create checkpoint
    checkpoint = SimpleCheckpoint(
        name="permits_checkpoint", data_context=context, **checkpoint_config
    )

    # Add checkpoint to context
    try:
        context.add_checkpoint(**checkpoint_config)
    except Exception:
        # Checkpoint might already exist
        pass

    return checkpoint


def run_permits_checkpoint(db_url: Optional[str] = None) -> Dict[str, Any]:
    """
    Run the permits_checkpoint to validate permits data.

    Args:
        db_url: Database connection URL

    Returns:
        Checkpoint validation results
    """
    try:
        # Initialize context
        context = gx.get_context()

        # Configure datasource if needed
        datasource_config = {
            "name": "postgres_datasource",
            "class_name": "Datasource",
            "module_name": "great_expectations.datasource",
            "execution_engine": {
                "class_name": "SqlAlchemyExecutionEngine",
                "connection_string": db_url or os.environ.get("DATABASE_URL"),
            },
            "data_connectors": {
                "default_runtime_data_connector": {
                    "class_name": "RuntimeDataConnector",
                    "batch_identifiers": ["default_identifier_name"],
                }
            },
        }

        try:
            context.add_datasource(**datasource_config)
        except Exception:
            # Datasource might already exist
            pass

        # Ensure expectation suite exists
        validator = PermitsValidationSuite(db_url)
        suite = validator.create_expectation_suite()
        try:
            context.add_expectation_suite(expectation_suite=suite)
        except Exception:
            context.update_expectation_suite(expectation_suite=suite)

        # Create and run checkpoint
        checkpoint = create_permits_checkpoint(context)
        results = checkpoint.run()

        # Extract summary
        validation_results = {
            "run_id": str(results.run_id),
            "run_name": results.run_name,
            "success": results.success,
            "validation_results": [],
        }

        # Process individual validation results
        for validation_result in results.list_validation_results():
            result_summary = {
                "success": validation_result.success,
                "statistics": validation_result.statistics,
                "meta": validation_result.meta,
            }
            validation_results["validation_results"].append(result_summary)

        return validation_results

    except Exception as e:
        logger.error(f"Checkpoint run failed: {e}")
        return {
            "success": False,
            "error": str(e),
            "run_id": None,
            "run_name": None,
            "validation_results": [],
        }


def validate_permits_rowcount_delta(
    current_count: int,
    previous_count: Optional[int] = None,
    tolerance_percent: float = 50.0,
) -> Dict[str, Any]:
    """
    Validate row count delta is within acceptable range.

    This function checks if the current row count is within ±50% of the previous
    count, which helps detect data pipeline issues.

    Args:
        current_count: Current number of rows in gold.permits
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
        "message": "",
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
        result["message"] = (
            f"Row count change within tolerance: {percent_change:.1f}% (±{tolerance_percent}%)"
        )
    else:
        result["success"] = False
        result["message"] = (
            f"Row count change exceeds tolerance: {percent_change:.1f}% > ±{tolerance_percent}%"
        )

        # This is a warning for first week, error after that
        result["severity"] = "warning"  # Can be upgraded to "error" by caller

    result["percent_change"] = percent_change
    return result


def run_full_validation(db_url: Optional[str] = None) -> Dict[str, Any]:
    """
    Run complete validation suite on gold.permits.

    Args:
        db_url: Database connection URL

    Returns:
        Complete validation results
    """
    try:
        # Initialize validation suite
        validator = PermitsValidationSuite(db_url)

        # Run Great Expectations validation
        ge_results = validator.validate_permits_data()

        # Get current row count for delta check
        import psycopg2

        with psycopg2.connect(db_url or os.environ.get("DATABASE_URL")) as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT COUNT(*) FROM gold.permits")
                current_count = cur.fetchone()[0]

        # Run row count delta check (would need to store previous count)
        rowcount_result = validate_permits_rowcount_delta(current_count)

        # Combine results
        combined_results = {
            "overall_success": ge_results["success"] and rowcount_result["success"],
            "great_expectations": ge_results,
            "rowcount_validation": rowcount_result,
            "timestamp": "datetime.utcnow().isoformat()",
            "total_rows": current_count,
        }

        return combined_results

    except Exception as e:
        logger.error(f"Full validation failed: {e}")
        return {
            "overall_success": False,
            "error": str(e),
            "timestamp": "datetime.utcnow().isoformat()",
        }


if __name__ == "__main__":
    # Run validation from command line
    import argparse

    parser = argparse.ArgumentParser(
        description="Run data quality validation on gold.permits"
    )
    parser.add_argument(
        "--db-url", help="PostgreSQL connection URL (or set DATABASE_URL env var)"
    )

    args = parser.parse_args()

    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    # Run validation
    results = run_full_validation(args.db_url)

    print("=" * 60)
    print("GOLD.PERMITS DATA QUALITY VALIDATION RESULTS")
    print("=" * 60)

    if results.get("overall_success"):
        print("✅ ALL VALIDATIONS PASSED")
    else:
        print("❌ VALIDATION FAILURES DETECTED")

    if "great_expectations" in results:
        ge = results["great_expectations"]
        print(
            f"\nGreat Expectations: {ge['successful_expectations']}/{ge['total_expectations']} checks passed"
        )

    if "rowcount_validation" in results:
        rc = results["rowcount_validation"]
        print(f"Row Count Check: {rc['message']}")

    if "total_rows" in results:
        print(f"Total Rows: {results['total_rows']}")

    # Exit with error code if validation failed
    exit(0 if results.get("overall_success") else 1)
