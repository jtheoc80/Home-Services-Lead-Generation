"""
Great Expectations data validation suite for Texas permit data.

This module defines data quality expectations and validation rules
for the Texas statewide permit ingestion pipeline.
"""

import great_expectations as ge
from great_expectations.checkpoint import SimpleCheckpoint
from datetime import datetime, timedelta
import os


def create_tx_permits_expectations():
    """Create Great Expectations suite for Texas permits data."""

    # Create context (would typically be configured separately)
    context = ge.get_context()

    # Define expectations for raw_permits table
    raw_permits_suite = context.create_expectation_suite(
        expectation_suite_name="tx_raw_permits_suite", overwrite_existing=True
    )

    # Key field expectations
    raw_permits_suite.add_expectation(
        ge.expectations.ExpectColumnToExist(column="source_id")
    )
    raw_permits_suite.add_expectation(
        ge.expectations.ExpectColumnToExist(column="raw_data")
    )
    raw_permits_suite.add_expectation(
        ge.expectations.ExpectColumnToExist(column="extracted_at")
    )

    # Data quality expectations
    raw_permits_suite.add_expectation(
        ge.expectations.ExpectColumnValuesToNotBeNull(column="source_id")
    )
    raw_permits_suite.add_expectation(
        ge.expectations.ExpectColumnValuesToNotBeNull(column="raw_data")
    )

    # Source ID should be from known sources
    raw_permits_suite.add_expectation(
        ge.expectations.ExpectColumnValuesToBeInSet(
            column="source_id",
            value_set=[
                "tx-harris-county",
                "tx-dallas-county",
                "tx-tarrant-county",
                "tx-bexar-county",
                "tx-houston-city",
                "tx-san-antonio-city",
                "tx-dallas-city",
                "tx-austin-city",
                "tx-fort-worth-city",
                "tx-el-paso-city",
                "tx-arlington-city",
                "tx-corpus-christi-city",
                "tx-plano-city",
                "tx-lubbock-city",
                "tx-houston-tpia",
            ],
        )
    )

    # Recent data should exist
    raw_permits_suite.add_expectation(
        ge.expectations.ExpectColumnValuesToBeBetween(
            column="extracted_at",
            min_value=datetime.now() - timedelta(days=7),
            max_value=datetime.now() + timedelta(hours=1),
        )
    )

    # Define expectations for normalized permits table
    permits_suite = context.create_expectation_suite(
        expectation_suite_name="tx_permits_suite", overwrite_existing=True
    )

    # Required fields
    permits_suite.add_expectation(
        ge.expectations.ExpectColumnToExist(column="permit_id")
    )
    permits_suite.add_expectation(
        ge.expectations.ExpectColumnToExist(column="source_id")
    )
    permits_suite.add_expectation(ge.expectations.ExpectColumnToExist(column="address"))

    # Permit ID should not be null
    permits_suite.add_expectation(
        ge.expectations.ExpectColumnValuesToNotBeNull(column="permit_id")
    )

    # Coordinates should be within Texas bounds when present
    permits_suite.add_expectation(
        ge.expectations.ExpectColumnValuesToBeBetween(
            column="latitude",
            min_value=25.0,
            max_value=37.0,
            mostly=0.95,  # Allow 5% to be outside bounds (data quality issues)
        )
    )
    permits_suite.add_expectation(
        ge.expectations.ExpectColumnValuesToBeBetween(
            column="longitude", min_value=-107.0, max_value=-93.0, mostly=0.95
        )
    )

    # Issue dates should be reasonable
    permits_suite.add_expectation(
        ge.expectations.ExpectColumnValuesToBeBetween(
            column="issue_date",
            min_value=datetime(1990, 1, 1).date(),
            max_value=(datetime.now() + timedelta(days=365)).date(),
            mostly=0.99,
        )
    )

    # Estimated cost should be positive when present
    permits_suite.add_expectation(
        ge.expectations.ExpectColumnValuesToBePositive(
            column="estimated_cost", mostly=0.98
        )
    )

    # Confidence score should be between 0 and 1
    permits_suite.add_expectation(
        ge.expectations.ExpectColumnValuesToBeBetween(
            column="confidence_score", min_value=0.0, max_value=1.0
        )
    )

    # State should be TX
    permits_suite.add_expectation(
        ge.expectations.ExpectColumnValuesToBeInSet(
            column="state",
            value_set=["TX", "TEXAS", None],  # Allow null values
            mostly=0.99,
        )
    )

    return context, [raw_permits_suite, permits_suite]


def create_validation_checkpoint():
    """Create a checkpoint for running all validations."""

    context = ge.get_context()

    # Create checkpoint configuration
    checkpoint_config = {
        "name": "tx_permits_checkpoint",
        "config_version": 1.0,
        "class_name": "SimpleCheckpoint",
        "run_name_template": "tx_permits_validation_%Y%m%d_%H%M%S",
        "validations": [
            {
                "batch_request": {
                    "datasource_name": "postgres_datasource",
                    "data_connector_name": "default_inferred_data_connector_name",
                    "data_asset_name": "raw_permits",
                },
                "expectation_suite_name": "tx_raw_permits_suite",
            },
            {
                "batch_request": {
                    "datasource_name": "postgres_datasource",
                    "data_connector_name": "default_inferred_data_connector_name",
                    "data_asset_name": "permits",
                },
                "expectation_suite_name": "tx_permits_suite",
            },
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

    checkpoint = SimpleCheckpoint(
        name="tx_permits_checkpoint", data_context=context, **checkpoint_config
    )

    context.add_checkpoint(**checkpoint_config)
    return checkpoint


def run_validation(db_url: str) -> dict:
    """Run Great Expectations validation on Texas permits data."""

    try:
        # Initialize Great Expectations context
        context = ge.get_context()

        # Configure datasource for PostgreSQL
        datasource_config = {
            "name": "postgres_datasource",
            "class_name": "Datasource",
            "execution_engine": {
                "class_name": "SqlAlchemyExecutionEngine",
                "connection_string": db_url,
            },
            "data_connectors": {
                "default_inferred_data_connector_name": {
                    "class_name": "InferredAssetSqlDataConnector",
                    "include_schema_name": True,
                }
            },
        }

        context.add_datasource(**datasource_config)

        # Create expectations
        context, suites = create_tx_permits_expectations()

        # Create and run checkpoint
        checkpoint = create_validation_checkpoint()

        # Run validation
        results = checkpoint.run()

        # Extract results
        validation_results = {
            "run_id": results.run_id,
            "run_name": results.run_name,
            "success": results.success,
            "statistics": {
                "evaluated_expectations": results.statistics["evaluated_expectations"],
                "successful_expectations": results.statistics[
                    "successful_expectations"
                ],
                "unsuccessful_expectations": results.statistics[
                    "unsuccessful_expectations"
                ],
                "success_percent": results.statistics["success_percent"],
            },
            "validation_results": [],
        }

        # Process individual validation results
        for validation_result in results.validation_results:
            result_summary = {
                "data_asset_name": validation_result.meta["batch_kwargs"]["table"],
                "expectation_suite_name": validation_result.meta[
                    "expectation_suite_name"
                ],
                "success": validation_result.success,
                "statistics": validation_result.statistics,
                "failed_expectations": [],
            }

            # Collect failed expectations
            for result in validation_result.results:
                if not result.success:
                    result_summary["failed_expectations"].append(
                        {
                            "expectation_type": result.expectation_config.expectation_type,
                            "column": result.expectation_config.kwargs.get("column"),
                            "result": result.result,
                        }
                    )

            validation_results["validation_results"].append(result_summary)

        return validation_results

    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "run_time": datetime.now().isoformat(),
        }


def main():
    """CLI entry point for running Great Expectations validation."""
    import argparse
    import json

    parser = argparse.ArgumentParser(
        description="Run Great Expectations validation on TX permits"
    )
    parser.add_argument(
        "--db-url", help="PostgreSQL connection URL (or set DATABASE_URL env var)"
    )
    parser.add_argument("--output", help="Output file for results (default: stdout)")

    args = parser.parse_args()

    # Get database URL
    db_url = args.db_url or os.environ.get("DATABASE_URL")
    if not db_url:
        print("Error: Database URL required (--db-url or DATABASE_URL env var)")
        return 1

    try:
        # Run validation
        results = run_validation(db_url)

        # Output results
        if args.output:
            with open(args.output, "w") as f:
                json.dump(results, f, indent=2, default=str)
            print(f"Validation results saved to {args.output}")
        else:
            print(json.dumps(results, indent=2, default=str))

        # Exit with error code if validation failed
        return 0 if results.get("success", False) else 1

    except Exception as e:
        print(f"Validation failed: {e}")
        return 1


if __name__ == "__main__":
    exit(main())
