#!/bin/bash

# Supabase Database and Storage Export Script
# This script exports the database schema, data, and storage buckets from Supabase
# for backup validation purposes.

set -euo pipefail

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKUP_DIR="${BACKUP_DIR:-${SCRIPT_DIR}/../backups}"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_NAME="supabase_backup_${TIMESTAMP}"

# Show usage
usage() {
    cat << EOF
Usage: $0 [OPTIONS]

Export Supabase database and storage for backup validation.

Options:
    -h, --help      Show this help message
    --dry-run       Show what would be done without executing
    --version       Show script version

Environment Variables:
    SUPABASE_URL                Production Supabase project URL (required)
    SUPABASE_SERVICE_ROLE       Production Supabase service role key (required)
    BACKUP_DIR                  Directory to store backups (default: ../backups)

Examples:
    export SUPABASE_URL="https://your-project.supabase.co"
    export SUPABASE_SERVICE_ROLE="your-service-role-key"
    $0

    # Dry run to see what would be done
    $0 --dry-run
EOF
}

# Parse command line arguments
DRY_RUN=false
while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help)
            usage
            exit 0
            ;;
        --dry-run)
            DRY_RUN=true
            shift
            ;;
        --version)
            echo "Supabase Backup Export v1.0.0"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            usage
            exit 1
            ;;
    esac
done

# Required environment variables (only check if not dry run)
if [ "$DRY_RUN" = "false" ]; then
    : "${SUPABASE_URL:?SUPABASE_URL environment variable is required}"
    : "${SUPABASE_SERVICE_ROLE:?SUPABASE_SERVICE_ROLE environment variable is required}"
fi

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

success() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] SUCCESS:${NC} $1"
}

warning() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] WARNING:${NC} $1"
}

error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ERROR:${NC} $1"
}

# Create backup directory
create_backup_dir() {
    log "Creating backup directory: ${BACKUP_DIR}/${BACKUP_NAME}"
    mkdir -p "${BACKUP_DIR}/${BACKUP_NAME}"
}

# Export database schema
export_database_schema() {
    log "Exporting database schema..."
    
    # Extract database connection details from Supabase URL
    DB_HOST=$(echo "$SUPABASE_URL" | sed 's|https://||' | sed 's|\.supabase\.co.*|.supabase.co|')
    DB_NAME="postgres"
    
    # Use pg_dump to export schema
    PGPASSWORD="$SUPABASE_SERVICE_ROLE" pg_dump \
        --host="db.${DB_HOST#https://}" \
        --port=5432 \
        --username=postgres \
        --dbname="$DB_NAME" \
        --schema-only \
        --no-owner \
        --no-privileges \
        --format=plain \
        --file="${BACKUP_DIR}/${BACKUP_NAME}/schema.sql" || {
        error "Failed to export database schema"
        return 1
    }
    
    success "Database schema exported to schema.sql"
}

# Export database data
export_database_data() {
    log "Exporting database data..."
    
    # Extract database connection details from Supabase URL
    DB_HOST=$(echo "$SUPABASE_URL" | sed 's|https://||' | sed 's|\.supabase\.co.*|.supabase.co|')
    DB_NAME="postgres"
    
    # Use pg_dump to export data
    PGPASSWORD="$SUPABASE_SERVICE_ROLE" pg_dump \
        --host="db.${DB_HOST#https://}" \
        --port=5432 \
        --username=postgres \
        --dbname="$DB_NAME" \
        --data-only \
        --no-owner \
        --no-privileges \
        --format=plain \
        --exclude-table-data="auth.*" \
        --exclude-table-data="realtime.*" \
        --exclude-table-data="storage.*" \
        --exclude-table-data="_realtime.*" \
        --file="${BACKUP_DIR}/${BACKUP_NAME}/data.sql" || {
        error "Failed to export database data"
        return 1
    }
    
    success "Database data exported to data.sql"
}

# Export specific tables critical to the application
export_critical_tables() {
    log "Exporting critical application tables..."
    
    local tables=("leads" "permits_raw_harris" "user_preferences" "notification_logs")
    
    for table in "${tables[@]}"; do
        log "Exporting table: $table"
        
        # Use Supabase REST API to export table data
        curl -s \
            -H "apikey: $SUPABASE_SERVICE_ROLE" \
            -H "Authorization: Bearer $SUPABASE_SERVICE_ROLE" \
            -H "Content-Type: application/json" \
            "${SUPABASE_URL}/rest/v1/${table}?select=*" \
            > "${BACKUP_DIR}/${BACKUP_NAME}/${table}.json" || {
            warning "Failed to export table: $table (table may not exist)"
            continue
        }
        
        # Check if export was successful
        if [ -s "${BACKUP_DIR}/${BACKUP_NAME}/${table}.json" ]; then
            local count=$(jq '. | length' "${BACKUP_DIR}/${BACKUP_NAME}/${table}.json" 2>/dev/null || echo "unknown")
            success "Exported $count records from table: $table"
        else
            warning "No data exported for table: $table"
        fi
    done
}

# Export storage buckets metadata (file listings)
export_storage_metadata() {
    log "Exporting storage buckets metadata..."
    
    # List all storage buckets
    curl -s \
        -H "apikey: $SUPABASE_SERVICE_ROLE" \
        -H "Authorization: Bearer $SUPABASE_SERVICE_ROLE" \
        "${SUPABASE_URL}/storage/v1/bucket" \
        > "${BACKUP_DIR}/${BACKUP_NAME}/storage_buckets.json" || {
        warning "Failed to export storage buckets list"
        return 0
    }
    
    # For each bucket, export file listings
    if [ -f "${BACKUP_DIR}/${BACKUP_NAME}/storage_buckets.json" ]; then
        local buckets=$(jq -r '.[].name' "${BACKUP_DIR}/${BACKUP_NAME}/storage_buckets.json" 2>/dev/null || echo "")
        
        for bucket in $buckets; do
            log "Exporting file list for bucket: $bucket"
            
            curl -s \
                -H "apikey: $SUPABASE_SERVICE_ROLE" \
                -H "Authorization: Bearer $SUPABASE_SERVICE_ROLE" \
                "${SUPABASE_URL}/storage/v1/object/list/${bucket}" \
                > "${BACKUP_DIR}/${BACKUP_NAME}/storage_${bucket}_files.json" || {
                warning "Failed to export file list for bucket: $bucket"
            }
        done
    fi
    
    success "Storage metadata exported"
}

# Create backup manifest with metadata
create_backup_manifest() {
    log "Creating backup manifest..."
    
    cat > "${BACKUP_DIR}/${BACKUP_NAME}/manifest.json" << EOF
{
  "backup_name": "${BACKUP_NAME}",
  "timestamp": "${TIMESTAMP}",
  "supabase_url": "${SUPABASE_URL}",
  "created_at": "$(date -u +"%Y-%m-%dT%H:%M:%S.%3NZ")",
  "backup_type": "validation",
  "purpose": "Monthly backup validation test",
  "files": {
    "schema": "schema.sql",
    "data": "data.sql",
    "tables": [
      "leads.json",
      "permits_raw_harris.json",
      "user_preferences.json",
      "notification_logs.json"
    ],
    "storage": {
      "buckets": "storage_buckets.json",
      "file_listings": "storage_*_files.json"
    }
  },
  "validation": {
    "restore_required": true,
    "smoke_test_required": true,
    "retention_days": 30
  }
}
EOF
    
    success "Backup manifest created"
}

# Compress backup for efficient storage
compress_backup() {
    log "Compressing backup..."
    
    cd "${BACKUP_DIR}"
    tar -czf "${BACKUP_NAME}.tar.gz" "${BACKUP_NAME}/" || {
        error "Failed to compress backup"
        return 1
    }
    
    # Calculate checksums
    sha256sum "${BACKUP_NAME}.tar.gz" > "${BACKUP_NAME}.tar.gz.sha256"
    
    success "Backup compressed to ${BACKUP_NAME}.tar.gz"
    
    # Display backup size
    local size=$(du -h "${BACKUP_NAME}.tar.gz" | cut -f1)
    log "Backup size: $size"
}

# Validate backup files
validate_backup() {
    log "Validating backup files..."
    
    local errors=0
    
    # Check required files exist
    local required_files=("schema.sql" "data.sql" "manifest.json")
    for file in "${required_files[@]}"; do
        if [ ! -f "${BACKUP_DIR}/${BACKUP_NAME}/${file}" ]; then
            error "Required file missing: $file"
            ((errors++))
        fi
    done
    
    # Check if compressed backup exists
    if [ ! -f "${BACKUP_DIR}/${BACKUP_NAME}.tar.gz" ]; then
        error "Compressed backup missing"
        ((errors++))
    fi
    
    # Validate JSON files
    for json_file in "${BACKUP_DIR}/${BACKUP_NAME}"/*.json; do
        if [ -f "$json_file" ]; then
            if ! jq empty "$json_file" >/dev/null 2>&1; then
                error "Invalid JSON file: $(basename "$json_file")"
                ((errors++))
            fi
        fi
    done
    
    if [ $errors -eq 0 ]; then
        success "Backup validation passed"
        return 0
    else
        error "Backup validation failed with $errors errors"
        return 1
    fi
}

# Cleanup old backups (keep last 5)
cleanup_old_backups() {
    log "Cleaning up old backups..."
    
    cd "${BACKUP_DIR}"
    
    # Remove old directories (keep last 5)
    ls -dt supabase_backup_*/ 2>/dev/null | tail -n +6 | xargs rm -rf
    
    # Remove old compressed backups (keep last 5)
    ls -dt supabase_backup_*.tar.gz 2>/dev/null | tail -n +6 | xargs rm -f
    ls -dt supabase_backup_*.tar.gz.sha256 2>/dev/null | tail -n +6 | xargs rm -f
    
    success "Old backups cleaned up"
}

# Main execution
main() {
    # Handle dry run mode
    if [ "$DRY_RUN" = "true" ]; then
        log "=== DRY RUN MODE ==="
        log "Would export Supabase backup with the following configuration:"
        log "  Backup directory: ${BACKUP_DIR}"
        log "  Backup name: ${BACKUP_NAME}"
        log "  Supabase URL: ${SUPABASE_URL:-'[not set]'}"
        log "  Service role: ${SUPABASE_SERVICE_ROLE:+[set]}${SUPABASE_SERVICE_ROLE:-[not set]}"
        log ""
        log "Steps that would be executed:"
        log "  1. Create backup directory"
        log "  2. Export database schema via pg_dump"
        log "  3. Export database data via pg_dump"
        log "  4. Export critical tables via REST API"
        log "  5. Export storage metadata via REST API"
        log "  6. Create backup manifest"
        log "  7. Compress backup to .tar.gz"
        log "  8. Validate backup files"
        log "  9. Cleanup old backups (keep last 5)"
        log ""
        log "To run for real, remove --dry-run flag"
        exit 0
    fi
    
    log "Starting Supabase backup export..."
    log "Backup name: ${BACKUP_NAME}"
    log "Supabase URL: ${SUPABASE_URL}"
    
    # Check dependencies
    if ! command -v pg_dump >/dev/null 2>&1; then
        error "pg_dump is required but not installed"
        exit 1
    fi
    
    if ! command -v curl >/dev/null 2>&1; then
        error "curl is required but not installed"
        exit 1
    fi
    
    if ! command -v jq >/dev/null 2>&1; then
        error "jq is required but not installed"
        exit 1
    fi
    
    # Execute backup steps
    create_backup_dir
    
    # Export database
    export_database_schema
    export_database_data
    
    # Export application data
    export_critical_tables
    
    # Export storage metadata
    export_storage_metadata
    
    # Create manifest and compress
    create_backup_manifest
    compress_backup
    
    # Validate backup
    if validate_backup; then
        success "Backup export completed successfully"
        log "Backup location: ${BACKUP_DIR}/${BACKUP_NAME}.tar.gz"
        
        # Cleanup old backups
        cleanup_old_backups
        
        exit 0
    else
        error "Backup export failed validation"
        exit 1
    fi
}

# Handle script termination
trap 'error "Backup export interrupted"; exit 1' INT TERM

# Run main function
main "$@"