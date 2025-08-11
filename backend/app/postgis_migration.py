"""
PostGIS migration utilities for LeadLedgerPro.

Handles optional PostGIS support for enhanced spatial queries.
"""

import os
import logging
from pathlib import Path
import psycopg2

logger = logging.getLogger(__name__)


def check_postgis_available(db_url: str) -> bool:
    """Check if PostGIS extension is available in the database."""
    try:
        conn = psycopg2.connect(db_url)
        cur = conn.cursor()
        
        # Check if PostGIS extension exists
        cur.execute("""
            SELECT 1 FROM pg_available_extensions 
            WHERE name = 'postgis' AND installed_version IS NOT NULL
        """)
        
        result = cur.fetchone()
        conn.close()
        
        return result is not None
        
    except Exception as e:
        logger.warning(f"Could not check PostGIS availability: {e}")
        return False


def enable_postgis_support(db_url: str, force: bool = False) -> bool:
    """
    Enable PostGIS support in the database.
    
    Args:
        db_url: Database connection string
        force: Whether to proceed even if USE_POSTGIS=false
        
    Returns:
        True if PostGIS was enabled, False otherwise
    """
    
    use_postgis = os.environ.get('USE_POSTGIS', 'false').lower() == 'true'
    
    if not use_postgis and not force:
        logger.info("PostGIS support disabled (USE_POSTGIS=false)")
        return False
    
    try:
        conn = psycopg2.connect(db_url)
        cur = conn.cursor()
        
        # Check if PostGIS is already enabled
        cur.execute("""
            SELECT 1 FROM pg_extension WHERE extname = 'postgis'
        """)
        
        if cur.fetchone():
            logger.info("PostGIS extension already enabled")
            postgis_enabled = True
        else:
            # Try to enable PostGIS
            try:
                cur.execute("CREATE EXTENSION IF NOT EXISTS postgis")
                conn.commit()
                logger.info("PostGIS extension enabled successfully")
                postgis_enabled = True
            except Exception as e:
                logger.warning(f"Could not enable PostGIS extension: {e}")
                postgis_enabled = False
        
        if postgis_enabled:
            # Add geometry column and index to leads table
            try:
                # Check if geometry column already exists
                cur.execute("""
                    SELECT 1 FROM information_schema.columns 
                    WHERE table_name = 'leads' AND column_name = 'geom'
                """)
                
                if not cur.fetchone():
                    # Add geometry column
                    cur.execute("""
                        ALTER TABLE leads 
                        ADD COLUMN geom geometry(Point, 4326)
                    """)
                    logger.info("Added geometry column to leads table")
                
                # Update existing records with geometry from lat/lon
                cur.execute("""
                    UPDATE leads 
                    SET geom = ST_SetSRID(ST_MakePoint(lon, lat), 4326)
                    WHERE lon IS NOT NULL AND lat IS NOT NULL AND geom IS NULL
                """)
                updated_rows = cur.rowcount
                if updated_rows > 0:
                    logger.info(f"Updated {updated_rows} records with geometry")
                
                # Create spatial index if it doesn't exist
                cur.execute("""
                    SELECT 1 FROM pg_indexes 
                    WHERE indexname = 'leads_gix'
                """)
                
                if not cur.fetchone():
                    cur.execute("""
                        CREATE INDEX leads_gix ON leads USING GIST(geom)
                    """)
                    logger.info("Created spatial index on leads.geom")
                
                conn.commit()
                return True
                
            except Exception as e:
                logger.error(f"Error setting up PostGIS columns/indexes: {e}")
                conn.rollback()
                return False
        
        conn.close()
        return postgis_enabled
        
    except Exception as e:
        logger.error(f"Error enabling PostGIS support: {e}")
        return False


def migrate_to_postgis(db_url: str) -> None:
    """Run PostGIS migration if enabled."""
    use_postgis = os.environ.get('USE_POSTGIS', 'false').lower() == 'true'
    
    if not use_postgis:
        logger.info("Skipping PostGIS migration (USE_POSTGIS=false)")
        return
    
    logger.info("Running PostGIS migration...")
    success = enable_postgis_support(db_url)
    
    if success:
        logger.info("PostGIS migration completed successfully")
    else:
        logger.warning("PostGIS migration failed - falling back to lat/lon columns")


def create_trigger_for_geom_update(db_url: str) -> None:
    """Create trigger to automatically update geom column when lat/lon changes."""
    
    use_postgis = os.environ.get('USE_POSTGIS', 'false').lower() == 'true'
    if not use_postgis:
        return
    
    try:
        conn = psycopg2.connect(db_url)
        cur = conn.cursor()
        
        # Create function to update geometry
        cur.execute("""
            CREATE OR REPLACE FUNCTION update_leads_geom()
            RETURNS TRIGGER AS $$
            BEGIN
                IF NEW.lat IS NOT NULL AND NEW.lon IS NOT NULL THEN
                    NEW.geom = ST_SetSRID(ST_MakePoint(NEW.lon, NEW.lat), 4326);
                ELSE
                    NEW.geom = NULL;
                END IF;
                RETURN NEW;
            END;
            $$ LANGUAGE plpgsql;
        """)
        
        # Create trigger
        cur.execute("""
            DROP TRIGGER IF EXISTS leads_geom_update_trigger ON leads;
            CREATE TRIGGER leads_geom_update_trigger
                BEFORE INSERT OR UPDATE OF lat, lon ON leads
                FOR EACH ROW
                EXECUTE FUNCTION update_leads_geom();
        """)
        
        conn.commit()
        conn.close()
        
        logger.info("Created PostGIS trigger for automatic geometry updates")
        
    except Exception as e:
        logger.warning(f"Could not create PostGIS trigger: {e}")


def main():
    """CLI interface for PostGIS migration."""
    import sys
    from argparse import ArgumentParser
    
    parser = ArgumentParser(description="PostGIS migration utilities")
    parser.add_argument("--check", action="store_true", help="Check PostGIS availability")
    parser.add_argument("--enable", action="store_true", help="Enable PostGIS support")
    parser.add_argument("--migrate", action="store_true", help="Run full PostGIS migration")
    parser.add_argument("--force", action="store_true", help="Force operation even if USE_POSTGIS=false")
    
    args = parser.parse_args()
    
    db_url = os.environ.get('DATABASE_URL')
    if not db_url:
        print("ERROR: DATABASE_URL environment variable not set")
        sys.exit(1)
    
    if args.check:
        available = check_postgis_available(db_url)
        print(f"PostGIS available: {available}")
    elif args.enable:
        success = enable_postgis_support(db_url, force=args.force)
        print(f"PostGIS enabled: {success}")
    elif args.migrate:
        migrate_to_postgis(db_url)
        create_trigger_for_geom_update(db_url)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()