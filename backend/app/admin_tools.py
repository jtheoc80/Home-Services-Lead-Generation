#!/usr/bin/env python3
"""
Admin tools for managing regions and jurisdictions in LeadLedgerPro.

Provides CLI interface for adding, editing, and managing multi-region configuration.
"""

import os
import sys
import json
import logging
from typing import Dict, Any, Optional, List
from argparse import ArgumentParser
from pathlib import Path

import psycopg2
from psycopg2.extras import RealDictCursor

# Ensure the parent directory containing permit_leads is in sys.path
current_dir = Path(__file__).resolve().parent
parent_dir = current_dir.parent
if str(parent_dir) not in sys.path:
    sys.path.insert(0, str(parent_dir))
from permit_leads.config_loader import get_config_loader, Region, Jurisdiction

logger = logging.getLogger(__name__)


class AdminManager:
    """Admin interface for region/jurisdiction management."""
    
    def __init__(self, db_url: str):
        """Initialize admin manager."""
        self.db_url = db_url
        self.config_loader = get_config_loader()
    
    def connect_db(self):
        """Create database connection."""
        return psycopg2.connect(self.db_url)
    
    def sync_regions_to_db(self) -> None:
        """Sync regions from registry to database."""
        regions = self.config_loader.regions
        
        conn = self.connect_db()
        try:
            cur = conn.cursor()
            
            for region in regions.values():
                # Get parent ID if exists
                parent_id = None
                if region.parent:
                    cur.execute("SELECT id FROM regions WHERE slug = %s", (region.parent,))
                    parent_row = cur.fetchone()
                    if parent_row:
                        parent_id = parent_row[0]
                
                # Upsert region
                cur.execute("""
                    INSERT INTO regions (slug, name, level, parent_id)
                    VALUES (%s, %s, %s, %s)
                    ON CONFLICT (slug) 
                    DO UPDATE SET 
                        name = EXCLUDED.name,
                        level = EXCLUDED.level,
                        parent_id = EXCLUDED.parent_id
                    RETURNING id
                """, (region.slug, region.name, region.level, parent_id))
                
                region_id = cur.fetchone()[0]
                logger.info(f"Synced region: {region.slug} -> {region_id}")
            
            conn.commit()
            logger.info("Region sync completed")
            
        except Exception as e:
            conn.rollback()
            logger.error(f"Error syncing regions: {e}")
            raise
        finally:
            conn.close()
    
    def sync_jurisdictions_to_db(self) -> None:
        """Sync jurisdictions from registry to database."""
        jurisdictions = self.config_loader.jurisdictions
        
        conn = self.connect_db()
        try:
            cur = conn.cursor()
            
            for jurisdiction in jurisdictions.values():
                # Get region ID
                cur.execute("SELECT id FROM regions WHERE slug = %s", (jurisdiction.region_slug,))
                region_row = cur.fetchone()
                if not region_row:
                    logger.error(f"Region not found for jurisdiction {jurisdiction.slug}: {jurisdiction.region_slug}")
                    continue
                
                region_id = region_row[0]
                
                # Upsert jurisdiction
                cur.execute("""
                    INSERT INTO jurisdictions (
                        slug, name, region_id, state, fips, timezone, 
                        data_provider, source_config, active
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (slug)
                    DO UPDATE SET
                        name = EXCLUDED.name,
                        region_id = EXCLUDED.region_id,
                        state = EXCLUDED.state,
                        fips = EXCLUDED.fips,
                        timezone = EXCLUDED.timezone,
                        data_provider = EXCLUDED.data_provider,
                        source_config = EXCLUDED.source_config,
                        active = EXCLUDED.active
                    RETURNING id
                """, (
                    jurisdiction.slug,
                    jurisdiction.name,
                    region_id,
                    jurisdiction.state,
                    jurisdiction.fips,
                    jurisdiction.timezone,
                    jurisdiction.provider,
                    json.dumps(jurisdiction.source_config),
                    jurisdiction.active
                ))
                
                jurisdiction_id = cur.fetchone()[0]
                logger.info(f"Synced jurisdiction: {jurisdiction.slug} -> {jurisdiction_id}")
            
            conn.commit()
            logger.info("Jurisdiction sync completed")
            
        except Exception as e:
            conn.rollback()
            logger.error(f"Error syncing jurisdictions: {e}")
            raise
        finally:
            conn.close()
    
    def sync_plans_to_db(self) -> None:
        """Sync plans from registry to database."""
        plans = self.config_loader.plans
        
        conn = self.connect_db()
        try:
            cur = conn.cursor()
            
            for plan in plans.values():
                # Upsert plan
                cur.execute("""
                    INSERT INTO plans (slug, name, monthly_price_cents, credits, scope)
                    VALUES (%s, %s, %s, %s, %s)
                    ON CONFLICT (slug)
                    DO UPDATE SET
                        name = EXCLUDED.name,
                        monthly_price_cents = EXCLUDED.monthly_price_cents,
                        credits = EXCLUDED.credits,
                        scope = EXCLUDED.scope
                    RETURNING id
                """, (plan.slug, plan.name, plan.monthly_price_cents, plan.credits, plan.scope))
                
                plan_id = cur.fetchone()[0]
                
                # Clear existing plan regions
                cur.execute("DELETE FROM plan_regions WHERE plan_id = %s", (plan_id,))
                
                # Add plan regions
                for region_slug in plan.regions:
                    cur.execute("SELECT id FROM regions WHERE slug = %s", (region_slug,))
                    region_row = cur.fetchone()
                    if region_row:
                        cur.execute("""
                            INSERT INTO plan_regions (plan_id, region_id)
                            VALUES (%s, %s)
                        """, (plan_id, region_row[0]))
                
                logger.info(f"Synced plan: {plan.slug} -> {plan_id}")
            
            conn.commit()
            logger.info("Plan sync completed")
            
        except Exception as e:
            conn.rollback()
            logger.error(f"Error syncing plans: {e}")
            raise
        finally:
            conn.close()
    
    def list_regions(self) -> List[Dict[str, Any]]:
        """List all regions from database."""
        conn = self.connect_db()
        try:
            cur = conn.cursor(cursor_factory=RealDictCursor)
            cur.execute("""
                SELECT r.*,
                       parent.slug as parent_slug,
                       parent.name as parent_name,
                       COUNT(j.id) as jurisdiction_count
                FROM regions r
                LEFT JOIN regions parent ON r.parent_id = parent.id
                LEFT JOIN jurisdictions j ON r.id = j.region_id
                GROUP BY r.id, r.slug, r.name, r.level, r.parent_id, r.created_at,
                         parent.slug, parent.name
                ORDER BY r.level, r.name
            """)
            return [dict(row) for row in cur.fetchall()]
        finally:
            conn.close()
    
    def list_jurisdictions(self, region_slug: Optional[str] = None) -> List[Dict[str, Any]]:
        """List jurisdictions, optionally filtered by region."""
        conn = self.connect_db()
        try:
            cur = conn.cursor(cursor_factory=RealDictCursor)
            
            query = """
                SELECT j.*,
                       r.slug as region_slug,
                       r.name as region_name,
                       COUNT(l.id) as lead_count
                FROM jurisdictions j
                LEFT JOIN regions r ON j.region_id = r.id
                LEFT JOIN leads l ON j.id = l.jurisdiction_id
            """
            
            params = []
            if region_slug:
                query += " WHERE r.slug = %s"
                params.append(region_slug)
            
            query += """
                GROUP BY j.id, j.slug, j.name, j.region_id, j.state, j.fips,
                         j.timezone, j.data_provider, j.source_config, j.active, j.created_at,
                         r.slug, r.name
                ORDER BY j.state, j.name
            """
            
            cur.execute(query, params)
            return [dict(row) for row in cur.fetchall()]
        finally:
            conn.close()
    
    def test_jurisdiction_config(self, jurisdiction_slug: str) -> Dict[str, Any]:
        """Test jurisdiction configuration by running a sample query."""
        jurisdiction = self.config_loader.get_jurisdiction(jurisdiction_slug)
        if not jurisdiction:
            return {"error": f"Jurisdiction not found: {jurisdiction_slug}"}
        
        try:
            from permit_leads.region_adapter import RegionAwareAdapter
            from datetime import datetime, timedelta
            
            adapter = RegionAwareAdapter()
            since = datetime.now() - timedelta(days=1)
            
            permits = adapter.scrape_jurisdiction(jurisdiction_slug, since, limit=5)
            
            return {
                "success": True,
                "jurisdiction": jurisdiction.name,
                "provider": jurisdiction.provider,
                "sample_permits": len(permits),
                "permits": [permit.dict() for permit in permits[:3]]  # First 3 for preview
            }
            
        except Exception as e:
            return {
                "error": str(e),
                "jurisdiction": jurisdiction.name,
                "provider": jurisdiction.provider
            }
    
    def update_jurisdiction_status(self, jurisdiction_slug: str, active: bool) -> bool:
        """Update jurisdiction active status."""
        conn = self.connect_db()
        try:
            cur = conn.cursor()
            cur.execute("""
                UPDATE jurisdictions 
                SET active = %s 
                WHERE slug = %s
            """, (active, jurisdiction_slug))
            
            if cur.rowcount > 0:
                conn.commit()
                logger.info(f"Updated {jurisdiction_slug} active status to {active}")
                return True
            else:
                logger.warning(f"Jurisdiction not found: {jurisdiction_slug}")
                return False
        except Exception as e:
            conn.rollback()
            logger.error(f"Error updating jurisdiction status: {e}")
            return False
        finally:
            conn.close()


def main():
    """CLI interface for admin tools."""
    parser = ArgumentParser(description="LeadLedgerPro Admin Tools")
    
    subparsers = parser.add_subparsers(dest="command", help="Admin commands")
    
    # Sync commands
    sync_parser = subparsers.add_parser("sync", help="Sync registry to database")
    sync_parser.add_argument("--regions", action="store_true", help="Sync regions")
    sync_parser.add_argument("--jurisdictions", action="store_true", help="Sync jurisdictions")
    sync_parser.add_argument("--plans", action="store_true", help="Sync plans")
    sync_parser.add_argument("--all", action="store_true", help="Sync all")
    
    # List commands
    list_parser = subparsers.add_parser("list", help="List entities")
    list_parser.add_argument("type", choices=["regions", "jurisdictions"], help="Entity type to list")
    list_parser.add_argument("--region", help="Filter jurisdictions by region")
    
    # Test commands
    test_parser = subparsers.add_parser("test", help="Test jurisdiction configuration")
    test_parser.add_argument("jurisdiction", help="Jurisdiction slug to test")
    
    # Status commands
    status_parser = subparsers.add_parser("status", help="Update jurisdiction status")
    status_parser.add_argument("jurisdiction", help="Jurisdiction slug")
    status_parser.add_argument("--active", action="store_true", help="Set as active")
    status_parser.add_argument("--inactive", action="store_true", help="Set as inactive")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    # Setup logging
    logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
    
    # Get database URL
    db_url = os.environ.get('DATABASE_URL')
    if not db_url:
        print("ERROR: DATABASE_URL environment variable not set")
        sys.exit(1)
    
    admin = AdminManager(db_url)
    
    try:
        if args.command == "sync":
            if args.all or args.regions:
                admin.sync_regions_to_db()
            if args.all or args.jurisdictions:
                admin.sync_jurisdictions_to_db()
            if args.all or args.plans:
                admin.sync_plans_to_db()
                
        elif args.command == "list":
            if args.type == "regions":
                regions = admin.list_regions()
                print(json.dumps(regions, indent=2, default=str))
            elif args.type == "jurisdictions":
                jurisdictions = admin.list_jurisdictions(args.region)
                print(json.dumps(jurisdictions, indent=2, default=str))
                
        elif args.command == "test":
            result = admin.test_jurisdiction_config(args.jurisdiction)
            print(json.dumps(result, indent=2, default=str))
            
        elif args.command == "status":
            if args.active and args.inactive:
                print("ERROR: Cannot specify both --active and --inactive")
                sys.exit(1)
            elif args.active:
                success = admin.update_jurisdiction_status(args.jurisdiction, True)
            elif args.inactive:
                success = admin.update_jurisdiction_status(args.jurisdiction, False)
            else:
                print("ERROR: Must specify either --active or --inactive")
                sys.exit(1)
                
            if not success:
                sys.exit(1)
    
    except Exception as e:
        logger.error(f"Admin command failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()