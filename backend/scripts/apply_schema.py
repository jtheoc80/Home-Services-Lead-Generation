#!/usr/bin/env python3
"""
Database schema application script for Home Services Lead Generation.

This script connects to the PostgreSQL database using $DATABASE_URL and applies
the schema from models.sql idempotently (skipping objects that already exist).
"""

import os
import sys
import logging
from pathlib import Path
from typing import Optional

import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
try:
    from dotenv import load_dotenv
except ImportError:
    print("Error: The 'python-dotenv' package is required to run this script. Please install it with 'pip install python-dotenv'.", file=sys.stderr)
    sys.exit(1)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def get_database_url() -> str:
    """Get database URL from environment variables."""
    # Try to load from .env file
    load_dotenv()
    
    db_url = os.getenv('DATABASE_URL')
    if not db_url:
        raise ValueError(
            "DATABASE_URL environment variable is not set. "
            "Please set it to your PostgreSQL connection string."
        )
    return db_url


def read_models_sql() -> str:
    """Read the models.sql file."""
    # Get the script directory and find models.sql
    script_dir = Path(__file__).parent
    models_path = script_dir.parent / "app" / "models.sql"
    
    if not models_path.exists():
        raise FileNotFoundError(f"models.sql not found at {models_path}")
    
    try:
        with open(models_path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        raise RuntimeError(f"Failed to read models.sql: {e}")


def apply_schema(db_url: str, sql_content: str) -> None:
    """Apply the schema to the database idempotently."""
    try:
        # Connect to database
        logger.info("Connecting to database...")
        conn = psycopg2.connect(db_url)
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        
        with conn.cursor() as cursor:
            logger.info("Applying schema from models.sql...")
            
            # Split the SQL content into individual statements for better error handling
            # and to make CREATE TYPE statements idempotent
            statements = [stmt.strip() for stmt in sql_content.split(';') if stmt.strip()]
            
            for statement in statements:
                # Skip empty statements and comments
                if not statement or statement.startswith('--'):
                    continue
                
                try:
                    # Handle CREATE TYPE statements to make them idempotent
                    if statement.upper().startswith('CREATE TYPE'):
                        # Extract the type name for idempotent handling
                        type_match = statement.split()
                        if len(type_match) >= 3:
                            type_name = type_match[2]
                            # Check if type already exists
                            cursor.execute(
                                "SELECT 1 FROM pg_type WHERE typname = %s",
                                (type_name,)
                            )
                            if cursor.fetchone():
                                logger.info(f"Type {type_name} already exists, skipping...")
                        # Extract the type name for idempotent handling (handle qualified names)
                        match = re.search(r'CREATE\s+TYPE\s+([a-zA-Z_][\w\.]*)', statement, re.IGNORECASE)
                        if match:
                            qualified_type_name = match.group(1)
                            if '.' in qualified_type_name:
                                schema_name, type_name = qualified_type_name.split('.', 1)
                                # Get namespace OID for schema
                                cursor.execute(
                                    "SELECT oid FROM pg_namespace WHERE nspname = %s",
                                    (schema_name,)
                                )
                                ns_row = cursor.fetchone()
                                if ns_row:
                                    ns_oid = ns_row[0]
                                    cursor.execute(
                                        "SELECT 1 FROM pg_type WHERE typname = %s AND typnamespace = %s",
                                        (type_name, ns_oid)
                                    )
                                    if cursor.fetchone():
                                        logger.info(f"Type {qualified_type_name} already exists, skipping...")
                                        continue
                            else:
                                type_name = qualified_type_name
                                cursor.execute(
                                    "SELECT 1 FROM pg_type WHERE typname = %s",
                                    (type_name,)
                                )
                                if cursor.fetchone():
                                    logger.info(f"Type {type_name} already exists, skipping...")
                                    continue
                    
                    # Execute the statement
                    cursor.execute(statement)
                    logger.debug(f"Executed: {statement[:100]}...")
                    
                except psycopg2.Error as e:
                    # For CREATE TYPE statements, if the error is about the type already existing,
                    # we can safely ignore it
                    # For CREATE TYPE statements, if the error code is for duplicate object (42710),
                    # we can safely ignore it
                    if e.pgcode == '42710' and statement.upper().startswith('CREATE TYPE'):
                        logger.info(f"Type already exists, continuing...")
                        continue
                    else:
                        logger.error(f"Error executing statement: {statement[:100]}...")
                        raise
            
            logger.info("Schema applied successfully!")
            
    except psycopg2.Error as e:
        logger.error(f"Database error: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise
    finally:
        if 'conn' in locals():
            conn.close()
            logger.info("Database connection closed.")


def main() -> None:
    """Main entry point."""
    try:
        logger.info("Starting schema application...")
        
        # Get database URL
        db_url = get_database_url()
        logger.info("Database URL loaded from environment.")
        
        # Read models.sql
        sql_content = read_models_sql()
        logger.info("models.sql content loaded successfully.")
        
        # Apply schema
        apply_schema(db_url, sql_content)
        
        logger.info("Schema application completed successfully!")
        
    except Exception as e:
        logger.error(f"Schema application failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()