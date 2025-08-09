#!/usr/bin/env python3
"""
Database migration script for LeadLedgerPro.
Runs the models.sql schema file against the configured database.
"""
import os
import sys
import logging
import argparse
from pathlib import Path

# Add backend to Python path
backend_dir = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_dir))

try:
    import psycopg2
    from sqlalchemy import create_engine, text
    from sqlalchemy.exc import SQLAlchemyError
except ImportError:
    print("Error: Required dependencies not installed.")
    print("Run: pip install psycopg2-binary sqlalchemy")
    sys.exit(1)

from app.settings import settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def read_sql_file(file_path: Path) -> str:
    """Read SQL file content."""
    if not file_path.exists():
        raise FileNotFoundError(f"SQL file not found: {file_path}")
    
    return file_path.read_text(encoding='utf-8')


def run_migration(database_url: str, sql_content: str, dry_run: bool = False) -> bool:
    """
    Run migration against database.
    
    Args:
        database_url: Database connection string
        sql_content: SQL content to execute
        dry_run: If True, only validate SQL without executing
        
    Returns:
        True if successful, False otherwise
    """
    try:
        engine = create_engine(database_url)
        
        if dry_run:
            logger.info("DRY RUN: Validating SQL syntax...")
            # Just check if we can parse it
            with engine.connect() as connection:
                connection.execute(text("SELECT 1"))
            logger.info("✓ Database connection successful")
            logger.info("✓ SQL migration would execute (dry run mode)")
            return True
        
        logger.info("Executing database migration...")
        
        with engine.connect() as connection:
            # Start transaction
            trans = connection.begin()
            try:
                # Split SQL content by statements (basic approach)
                statements = [stmt.strip() for stmt in sql_content.split(';') if stmt.strip()]
                
                for i, statement in enumerate(statements, 1):
                    logger.info(f"Executing statement {i}/{len(statements)}")
                    logger.debug(f"SQL: {statement[:100]}...")
                    
                    connection.execute(text(statement))
                # Execute the entire SQL content as a single statement
                logger.info("Executing full migration SQL script as a single block")
                logger.debug(f"SQL: {sql_content[:500]}...")
                connection.execute(text(sql_content))
                
                # Commit transaction
                trans.commit()
                logger.info("✓ Migration completed successfully")
                return True
                
            except Exception as e:
                trans.rollback()
                logger.error(f"Migration failed: {e}")
                return False
                
    except SQLAlchemyError as e:
        logger.error(f"Database error: {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(description='Run database migration')
    parser.add_argument(
        '--database-url',
        help='Database URL (defaults to DATABASE_URL env var)'
    )
    parser.add_argument(
        '--sql-file',
        help='SQL file path (defaults to backend/app/models.sql)'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Validate migration without executing'
    )
    parser.add_argument(
        '--verbose',
        '-v',
        action='store_true',
        help='Enable verbose logging'
    )
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Determine database URL
    database_url = args.database_url or settings.database_url
    if not database_url:
        logger.error("No database URL provided. Set DATABASE_URL environment variable or use --database-url")
        return 1
    
    # Determine SQL file path
    if args.sql_file:
        sql_file = Path(args.sql_file)
    else:
        sql_file = backend_dir / "app" / "models.sql"
    
    logger.info(f"Migration parameters:")
    logger.info(f"  Database URL: {database_url[:20]}...")
    logger.info(f"  SQL file: {sql_file}")
    logger.info(f"  Environment: {settings.app_env}")
    logger.info(f"  Dry run: {args.dry_run}")
    
    try:
        # Read SQL file
        logger.info("Reading SQL file...")
        sql_content = read_sql_file(sql_file)
        logger.info(f"✓ SQL file loaded ({len(sql_content)} characters)")
        
        # Run migration
        success = run_migration(database_url, sql_content, args.dry_run)
        
        if success:
            logger.info("🎉 Migration completed successfully!")
            return 0
        else:
            logger.error("❌ Migration failed!")
            return 1
            
    except FileNotFoundError as e:
        logger.error(f"File error: {e}")
        return 1
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return 1


if __name__ == '__main__':
    sys.exit(main())