#!/bin/bash

# =============================================================================
# Home Services Lead Generation - System Diagnosis Script
# =============================================================================
# This script checks:
# - Environment variables presence
# - Database connectivity (Supabase and SQLite)
# - Pending migrations status
# - Scraper last run information
# - Provides actionable hints with proper exit codes
#
# Exit codes:
# 0 = All checks passed
# 1 = Warnings found (system operational but may have issues)
# 2 = Critical errors found (system likely non-operational)
# =============================================================================

set -e

# Script configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
EXIT_CODE=0
WARNINGS=0
ERRORS=0

# Colors for output
RED='\033[0;31m'
YELLOW='\033[1;33m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[PASS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARN]${NC} $1"
    WARNINGS=$((WARNINGS + 1))
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
    ERRORS=$((ERRORS + 1))
}

log_hint() {
    echo -e "  ${BLUE}💡 Hint:${NC} $1"
}

# Header
echo "============================================================================="
echo "Home Services Lead Generation - System Diagnosis"
echo "============================================================================="
echo "Checking system health and configuration..."
echo ""

# =============================================================================
# 1. Environment Variables Check
# =============================================================================
log_info "Checking environment variables..."

# Load .env file if it exists
ENV_FILE="$PROJECT_ROOT/.env"
if [[ -f "$ENV_FILE" ]]; then
    log_success "Found .env file at $ENV_FILE"
    set -o allexport
    source "$ENV_FILE"
    set +o allexport
else
    log_warning "No .env file found at $ENV_FILE"
    log_hint "Create a .env file based on .env.example to configure the application"
fi

# Critical environment variables
CRITICAL_VARS=(
    "SUPABASE_URL"
    "SUPABASE_SERVICE_ROLE"
)

# Optional but important environment variables
OPTIONAL_VARS=(
    "DATABASE_URL"
    "REDIS_URL"
    "GEOCODER"
    "MAPBOX_TOKEN"
    "GOOGLE_MAPS_API_KEY"
    "SENDGRID_API_KEY"
    "TWILIO_SID"
    "TWILIO_TOKEN"
)

# Check critical variables
for var in "${CRITICAL_VARS[@]}"; do
    if [[ -z "${!var}" ]]; then
        log_error "Critical environment variable $var is not set"
        log_hint "Set $var in your .env file or environment"
    else
        log_success "Critical variable $var is set"
    fi
done

# Check optional variables
missing_optional=()
for var in "${OPTIONAL_VARS[@]}"; do
    if [[ -z "${!var}" ]]; then
        missing_optional+=("$var")
    else
        log_success "Optional variable $var is set"
    fi
done

if [[ ${#missing_optional[@]} -gt 0 ]]; then
    log_warning "Missing optional environment variables: ${missing_optional[*]}"
    log_hint "These variables may be needed for full functionality. Check .env.example for details"
fi

echo ""

# =============================================================================
# 2. Database Connectivity Check
# =============================================================================
log_info "Checking database connectivity..."

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    log_error "Python3 is not available"
    log_hint "Install Python3 to run database connectivity checks"
else
    # Test Supabase connectivity
    if [[ -n "$SUPABASE_URL" && -n "$SUPABASE_SERVICE_ROLE" ]]; then
        cat > /tmp/test_supabase.py << 'EOF'
import os
import sys
import asyncio
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

try:
    from backend.app.supabase_client import get_supabase_client
    
    def test_supabase():
        try:
            supabase = get_supabase_client()
            # Test with a simple query - try to list tables or do a minimal operation
            result = supabase.table('users').select('id').limit(1).execute()
            return True, "Supabase connection successful"
        except Exception as e:
            return False, f"Supabase connection failed: {str(e)}"
    
    success, message = test_supabase()
    if success:
        print("PASS: " + message)
        sys.exit(0)
    else:
        print("FAIL: " + message)
        sys.exit(1)
        
except ImportError as e:
    print(f"FAIL: Cannot import Supabase client: {e}")
    sys.exit(1)
except Exception as e:
    print(f"FAIL: Unexpected error: {e}")
    sys.exit(1)
EOF

        cd "$PROJECT_ROOT"
        if python3 /tmp/test_supabase.py 2>/dev/null; then
            log_success "Supabase database connectivity verified"
        else
            log_error "Supabase database connection failed"
            log_hint "Check SUPABASE_URL and SUPABASE_SERVICE_ROLE environment variables"
            log_hint "Verify Supabase service is running and accessible"
        fi
        rm -f /tmp/test_supabase.py
    else
        log_warning "Supabase credentials not configured - skipping connectivity test"
    fi

    # Check SQLite database for permits
    SQLITE_DB="$PROJECT_ROOT/data/permits/permits.db"
    if [[ -f "$SQLITE_DB" ]]; then
        if command -v sqlite3 &> /dev/null; then
            if sqlite3 "$SQLITE_DB" "SELECT COUNT(*) FROM permits LIMIT 1;" &> /dev/null; then
                log_success "SQLite permits database is accessible"
            else
                log_warning "SQLite permits database exists but may be corrupted"
                log_hint "Check database integrity with: sqlite3 $SQLITE_DB 'PRAGMA integrity_check;'"
            fi
        else
            log_warning "sqlite3 command not available - cannot test SQLite database"
            log_hint "Install sqlite3 to perform database checks"
        fi
    else
        log_warning "SQLite permits database not found at $SQLITE_DB"
        log_hint "Run the permit scraper to create the database"
    fi
fi

echo ""

# =============================================================================
# 3. Migration Status Check
# =============================================================================
log_info "Checking migration status..."

MIGRATION_DIR="$PROJECT_ROOT/backend/app/migrations"
if [[ -d "$MIGRATION_DIR" ]]; then
    migration_files=($(find "$MIGRATION_DIR" -name "*.sql" | sort))
    log_success "Found ${#migration_files[@]} migration files"
    
    for migration in "${migration_files[@]}"; do
        filename=$(basename "$migration")
        log_info "  - $filename"
    done
    
    # Check if we can determine applied migrations
    if [[ -n "$SUPABASE_URL" && -n "$SUPABASE_SERVICE_ROLE" ]] && command -v python3 &> /dev/null; then
        cat > /tmp/check_migrations.py << 'EOF'
import os
import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

try:
    from backend.app.supabase_client import get_supabase_client
    
    def check_migration_table():
        try:
            supabase = get_supabase_client()
            # Try to query a migrations table if it exists
            # This is a common pattern - check for schema_migrations or similar
            tables = ['schema_migrations', 'migrations', 'applied_migrations']
            
            for table_name in tables:
                try:
                    result = supabase.table(table_name).select('*').limit(1).execute()
                    return True, f"Migration tracking table '{table_name}' found"
                except:
                    continue
            
            return False, "No migration tracking table found"
            
        except Exception as e:
            return False, f"Cannot check migration status: {str(e)}"
    
    success, message = check_migration_table()
    print(message)
    sys.exit(0 if success else 1)
        
except Exception as e:
    print(f"Cannot check migrations: {e}")
    sys.exit(1)
EOF

        cd "$PROJECT_ROOT"
        if python3 /tmp/check_migrations.py 2>/dev/null; then
            log_success "Migration tracking system appears to be in place"
        else
            log_warning "Cannot determine migration status"
            log_hint "Consider implementing a migration tracking system"
            log_hint "Run: python3 backend/scripts/apply_schema.py to apply schema"
        fi
        rm -f /tmp/check_migrations.py
    else
        log_warning "Cannot check migration status - database not configured"
    fi
else
    log_warning "Migration directory not found at $MIGRATION_DIR"
fi

echo ""

# =============================================================================
# 4. Scraper Last Run Check
# =============================================================================
log_info "Checking scraper last run status..."

# Check if permit scraper has been run recently
if [[ -f "$SQLITE_DB" ]] && command -v sqlite3 &> /dev/null; then
    last_scraped=$(sqlite3 "$SQLITE_DB" "SELECT MAX(scraped_at) FROM permits;" 2>/dev/null || echo "")
    
    if [[ -n "$last_scraped" && "$last_scraped" != "" ]]; then
        log_success "Last scraper run: $last_scraped"
        
        # Check if it's recent (within last 7 days)
        if command -v date &> /dev/null; then
            # Try to parse the date and check if it's recent
            current_time=$(date +%s)
            if [[ "$OSTYPE" == "darwin"* ]]; then
                # macOS date command
                last_time=$(date -j -f "%Y-%m-%d %H:%M:%S" "${last_scraped:0:19}" +%s 2>/dev/null || echo "0")
            else
                # Linux date command
                last_time=$(date -d "${last_scraped:0:19}" +%s 2>/dev/null || echo "0")
            fi
            
            if [[ "$last_time" -gt 0 ]]; then
                days_ago=$(( (current_time - last_time) / 86400 ))
                if [[ $days_ago -gt 7 ]]; then
                    log_warning "Last scraper run was $days_ago days ago"
                    log_hint "Consider running the permit scraper: python3 -m permit_leads"
                else
                    log_success "Scraper last run is recent ($days_ago days ago)"
                fi
            fi
        fi
        
        # Check total number of permits
        permit_count=$(sqlite3 "$SQLITE_DB" "SELECT COUNT(*) FROM permits;" 2>/dev/null || echo "0")
        log_info "Total permits in database: $permit_count"
        
        if [[ "$permit_count" -eq 0 ]]; then
            log_warning "No permits found in database"
            log_hint "Run the permit scraper to collect data: python3 -m permit_leads"
        fi
        
    else
        log_warning "No scraper run data found"
        log_hint "Run the permit scraper to collect data: python3 -m permit_leads"
    fi
else
    log_warning "Cannot check scraper status - SQLite database not accessible"
    log_hint "Ensure the permit scraper has been run at least once"
fi

echo ""

# =============================================================================
# 5. Additional Health Checks
# =============================================================================
log_info "Performing additional health checks..."

# Check if required Python packages are installed
if command -v python3 &> /dev/null; then
    cd "$PROJECT_ROOT"
    
    # Check backend requirements
    if [[ -f "backend/requirements.txt" ]]; then
        missing_packages=()
        while IFS= read -r line; do
            # Skip empty lines and comments
            [[ -z "$line" || "$line" =~ ^[[:space:]]*# ]] && continue
            
            # Extract package name (before any version specifiers)
            package=$(echo "$line" | sed 's/[>=<].*//' | sed 's/\[.*//')
            
            if ! python3 -c "import $package" &> /dev/null; then
                missing_packages+=("$package")
            fi
        done < "backend/requirements.txt"
        
        if [[ ${#missing_packages[@]} -eq 0 ]]; then
            log_success "All backend Python dependencies appear to be installed"
        else
            log_warning "Missing Python packages: ${missing_packages[*]}"
            log_hint "Install missing packages: pip install -r backend/requirements.txt"
        fi
    fi
    
    # Check permit_leads requirements
    if [[ -f "permit_leads/requirements.txt" ]]; then
        log_info "Permit leads requirements file found"
    fi
else
    log_warning "Python3 not available for dependency checks"
fi

# Check if Node.js dependencies are needed
if [[ -f "$PROJECT_ROOT/package.json" ]]; then
    if [[ -d "$PROJECT_ROOT/node_modules" ]]; then
        log_success "Node.js dependencies appear to be installed"
    else
        log_warning "Node.js dependencies not installed"
        log_hint "Run: npm install"
    fi
fi

echo ""

# =============================================================================
# Summary and Exit
# =============================================================================
echo "============================================================================="
echo "Diagnosis Summary"
echo "============================================================================="

if [[ $ERRORS -gt 0 ]]; then
    log_error "Found $ERRORS critical errors"
    EXIT_CODE=2
elif [[ $WARNINGS -gt 0 ]]; then
    log_warning "Found $WARNINGS warnings"
    EXIT_CODE=1
else
    log_success "All checks passed!"
    EXIT_CODE=0
fi

echo ""
echo "Exit code: $EXIT_CODE"
case $EXIT_CODE in
    0) echo "✅ System appears to be healthy and ready for operation" ;;
    1) echo "⚠️  System is operational but has warnings that should be addressed" ;;
    2) echo "❌ System has critical errors that need immediate attention" ;;
esac

echo ""
echo "For more help:"
echo "  - Check README.md for setup instructions"
echo "  - Review .env.example for required environment variables"
echo "  - Run 'make help' if a Makefile is available"
echo "============================================================================="

exit $EXIT_CODE