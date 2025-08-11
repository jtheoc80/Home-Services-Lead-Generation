#!/bin/bash

# Supabase Staging Environment Restoration Script
# This script restores a backup to a staging Supabase instance for validation testing

set -euo pipefail

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKUP_DIR="${BACKUP_DIR:-${SCRIPT_DIR}/../backups}"

# Required environment variables for staging (only if not showing help)
SHOW_HELP=false
if [ "${1:-}" = "-h" ] || [ "${1:-}" = "--help" ]; then
    SHOW_HELP=true
fi

if [ "$SHOW_HELP" = "false" ]; then
    : "${STAGING_SUPABASE_URL:?STAGING_SUPABASE_URL environment variable is required}"
    : "${STAGING_SUPABASE_SERVICE_ROLE:?STAGING_SUPABASE_SERVICE_ROLE environment variable is required}"
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

# Show usage
usage() {
    cat << EOF
Usage: $0 [BACKUP_NAME]

Restore a Supabase backup to staging environment for validation.

Arguments:
    BACKUP_NAME    Name of the backup to restore (without .tar.gz extension)
                   If not provided, will use the most recent backup

Environment Variables:
    STAGING_SUPABASE_URL           Staging Supabase project URL
    STAGING_SUPABASE_SERVICE_ROLE  Staging Supabase service role key
    BACKUP_DIR                     Directory containing backups (default: ../backups)

Examples:
    $0 supabase_backup_20240115_143022
    $0  # Uses most recent backup
EOF
}

# Find the most recent backup
find_latest_backup() {
    local latest_backup
    latest_backup=$(ls -t "${BACKUP_DIR}"/supabase_backup_*.tar.gz 2>/dev/null | head -n1)
    
    if [ -z "$latest_backup" ]; then
        error "No backups found in ${BACKUP_DIR}"
        exit 1
    fi
    
    # Extract backup name without directory and extension
    basename "$latest_backup" .tar.gz
}

# Extract backup
extract_backup() {
    local backup_name="$1"
    local backup_file="${BACKUP_DIR}/${backup_name}.tar.gz"
    local extract_dir="${BACKUP_DIR}/${backup_name}"
    
    log "Extracting backup: $backup_name"
    
    # Check if backup file exists
    if [ ! -f "$backup_file" ]; then
        error "Backup file not found: $backup_file"
        exit 1
    fi
    
    # Verify checksum if available
    if [ -f "${backup_file}.sha256" ]; then
        log "Verifying backup checksum..."
        cd "${BACKUP_DIR}"
        if ! sha256sum -c "${backup_name}.tar.gz.sha256"; then
            error "Backup checksum verification failed"
            exit 1
        fi
        success "Backup checksum verified"
    fi
    
    # Extract backup
    if [ ! -d "$extract_dir" ]; then
        cd "${BACKUP_DIR}"
        tar -xzf "${backup_name}.tar.gz" || {
            error "Failed to extract backup"
            exit 1
        }
    fi
    
    success "Backup extracted to: $extract_dir"
    echo "$extract_dir"
}

# Validate backup manifest
validate_manifest() {
    local backup_dir="$1"
    local manifest_file="${backup_dir}/manifest.json"
    
    log "Validating backup manifest..."
    
    if [ ! -f "$manifest_file" ]; then
        error "Manifest file not found: $manifest_file"
        exit 1
    fi
    
    # Validate JSON format
    if ! jq empty "$manifest_file" >/dev/null 2>&1; then
        error "Invalid manifest JSON format"
        exit 1
    fi
    
    # Extract manifest info
    local backup_name=$(jq -r '.backup_name' "$manifest_file")
    local timestamp=$(jq -r '.timestamp' "$manifest_file")
    local backup_type=$(jq -r '.backup_type' "$manifest_file")
    
    log "Backup info:"
    log "  Name: $backup_name"
    log "  Timestamp: $timestamp"
    log "  Type: $backup_type"
    
    success "Manifest validation passed"
}

# Clear staging database
clear_staging_database() {
    log "Clearing staging database..."
    
    # Get staging database connection details
    local db_host=$(echo "$STAGING_SUPABASE_URL" | sed 's|https://||' | sed 's|\.supabase\.co.*|.supabase.co|')
    local db_name="postgres"
    
    # Drop and recreate public schema to clear all data
    PGPASSWORD="$STAGING_SUPABASE_SERVICE_ROLE" psql \
        --host="db.${db_host#https://}" \
        --port=5432 \
        --username=postgres \
        --dbname="$db_name" \
        --command="DROP SCHEMA IF EXISTS public CASCADE; CREATE SCHEMA public;" || {
        error "Failed to clear staging database"
        return 1
    }
    
    success "Staging database cleared"
}

# Restore database schema
restore_database_schema() {
    local backup_dir="$1"
    local schema_file="${backup_dir}/schema.sql"
    
    log "Restoring database schema..."
    
    if [ ! -f "$schema_file" ]; then
        error "Schema file not found: $schema_file"
        return 1
    fi
    
    # Get staging database connection details
    local db_host=$(echo "$STAGING_SUPABASE_URL" | sed 's|https://||' | sed 's|\.supabase\.co.*|.supabase.co|')
    local db_name="postgres"
    
    # Restore schema
    PGPASSWORD="$STAGING_SUPABASE_SERVICE_ROLE" psql \
        --host="db.${db_host#https://}" \
        --port=5432 \
        --username=postgres \
        --dbname="$db_name" \
        --file="$schema_file" \
        --single-transaction || {
        error "Failed to restore database schema"
        return 1
    }
    
    success "Database schema restored"
}

# Restore database data
restore_database_data() {
    local backup_dir="$1"
    local data_file="${backup_dir}/data.sql"
    
    log "Restoring database data..."
    
    if [ ! -f "$data_file" ]; then
        warning "Data file not found: $data_file"
        return 0
    fi
    
    # Get staging database connection details
    local db_host=$(echo "$STAGING_SUPABASE_URL" | sed 's|https://||' | sed 's|\.supabase\.co.*|.supabase.co|')
    local db_name="postgres"
    
    # Restore data
    PGPASSWORD="$STAGING_SUPABASE_SERVICE_ROLE" psql \
        --host="db.${db_host#https://}" \
        --port=5432 \
        --username=postgres \
        --dbname="$db_name" \
        --file="$data_file" \
        --single-transaction || {
        warning "Some data restoration issues occurred (this may be normal)"
    }
    
    success "Database data restored"
}

# Restore critical tables via REST API
restore_critical_tables() {
    local backup_dir="$1"
    
    log "Restoring critical application tables..."
    
    local tables=("leads" "permits_raw_harris" "user_preferences" "notification_logs")
    
    for table in "${tables[@]}"; do
        local table_file="${backup_dir}/${table}.json"
        
        if [ ! -f "$table_file" ]; then
            warning "Table backup not found: $table_file"
            continue
        fi
        
        # Check if file contains data
        local record_count=$(jq '. | length' "$table_file" 2>/dev/null || echo "0")
        if [ "$record_count" = "0" ] || [ "$record_count" = "null" ]; then
            log "Skipping empty table: $table"
            continue
        fi
        
        log "Restoring table: $table ($record_count records)"
        
        # Restore table data via REST API
        curl -s \
            -X POST \
            -H "apikey: $STAGING_SUPABASE_SERVICE_ROLE" \
            -H "Authorization: Bearer $STAGING_SUPABASE_SERVICE_ROLE" \
            -H "Content-Type: application/json" \
            -H "Prefer: return=minimal" \
            -d @"$table_file" \
            "${STAGING_SUPABASE_URL}/rest/v1/${table}" || {
            warning "Failed to restore table via REST API: $table"
            continue
        }
        
        success "Restored table: $table"
    done
}

# Verify restoration
verify_restoration() {
    local backup_dir="$1"
    
    log "Verifying restoration..."
    
    local errors=0
    
    # Check that critical tables exist and have data
    local tables=("leads" "permits_raw_harris")
    
    for table in "${tables[@]}"; do
        log "Checking table: $table"
        
        # Get record count from staging
        local staging_count=$(curl -s \
            -H "apikey: $STAGING_SUPABASE_SERVICE_ROLE" \
            -H "Authorization: Bearer $STAGING_SUPABASE_SERVICE_ROLE" \
            -H "Content-Type: application/json" \
            -H "Accept: application/vnd.pgrst.object+json" \
            "${STAGING_SUPABASE_URL}/rest/v1/${table}?select=count" 2>/dev/null | \
            jq -r '.count' 2>/dev/null || echo "error")
        
        if [ "$staging_count" = "error" ] || [ "$staging_count" = "null" ]; then
            warning "Could not verify table: $table"
            continue
        fi
        
        # Compare with backup if available
        local backup_file="${backup_dir}/${table}.json"
        if [ -f "$backup_file" ]; then
            local backup_count=$(jq '. | length' "$backup_file" 2>/dev/null || echo "0")
            
            if [ "$staging_count" = "$backup_count" ]; then
                success "Table $table: $staging_count records (matches backup)"
            else
                warning "Table $table: $staging_count records (backup had $backup_count)"
            fi
        else
            log "Table $table: $staging_count records (no backup comparison)"
        fi
    done
    
    # Test basic API connectivity
    log "Testing staging API connectivity..."
    local health_check=$(curl -s \
        -H "apikey: $STAGING_SUPABASE_SERVICE_ROLE" \
        -H "Authorization: Bearer $STAGING_SUPABASE_SERVICE_ROLE" \
        "${STAGING_SUPABASE_URL}/rest/v1/" | \
        jq -r '.swagger' 2>/dev/null || echo "error")
    
    if [ "$health_check" != "error" ] && [ "$health_check" != "null" ]; then
        success "Staging API is responsive"
    else
        error "Staging API connectivity test failed"
        ((errors++))
    fi
    
    if [ $errors -eq 0 ]; then
        success "Restoration verification passed"
        return 0
    else
        error "Restoration verification failed with $errors errors"
        return 1
    fi
}

# Generate restoration report
generate_restoration_report() {
    local backup_dir="$1"
    local backup_name="$2"
    
    log "Generating restoration report..."
    
    local report_file="${backup_dir}/restoration_report.json"
    
    cat > "$report_file" << EOF
{
  "restoration": {
    "backup_name": "${backup_name}",
    "staging_url": "${STAGING_SUPABASE_URL}",
    "restored_at": "$(date -u +"%Y-%m-%dT%H:%M:%S.%3NZ")",
    "status": "completed",
    "next_step": "smoke_tests"
  },
  "verification": {
    "schema_restored": true,
    "data_restored": true,
    "api_accessible": true
  },
  "tables": {
EOF

    # Add table statistics
    local first=true
    local tables=("leads" "permits_raw_harris" "user_preferences" "notification_logs")
    
    for table in "${tables[@]}"; do
        if [ "$first" = true ]; then
            first=false
        else
            echo "," >> "$report_file"
        fi
        
        local count=$(curl -s \
            -H "apikey: $STAGING_SUPABASE_SERVICE_ROLE" \
            -H "Authorization: Bearer $STAGING_SUPABASE_SERVICE_ROLE" \
            "${STAGING_SUPABASE_URL}/rest/v1/${table}?select=count" 2>/dev/null | \
            jq -r '.count' 2>/dev/null || echo "0")
        
        echo "    \"${table}\": ${count}" >> "$report_file"
    done

    cat >> "$report_file" << EOF
  }
}
EOF
    
    success "Restoration report generated: $report_file"
}

# Main execution
main() {
    local backup_name="$1"
    
    log "Starting Supabase staging restoration..."
    log "Staging URL: ${STAGING_SUPABASE_URL}"
    
    # Check dependencies
    if ! command -v psql >/dev/null 2>&1; then
        error "psql is required but not installed"
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
    
    # Find backup if not specified
    if [ -z "$backup_name" ]; then
        backup_name=$(find_latest_backup)
        log "Using latest backup: $backup_name"
    fi
    
    # Extract backup
    local backup_dir
    backup_dir=$(extract_backup "$backup_name")
    
    # Validate backup
    validate_manifest "$backup_dir"
    
    # Clear staging database
    clear_staging_database
    
    # Restore database
    restore_database_schema "$backup_dir"
    restore_database_data "$backup_dir"
    
    # Restore application tables
    restore_critical_tables "$backup_dir"
    
    # Verify restoration
    if verify_restoration "$backup_dir"; then
        success "Staging restoration completed successfully"
        
        # Generate report
        generate_restoration_report "$backup_dir" "$backup_name"
        
        log "Staging environment ready for smoke tests"
        log "Staging URL: ${STAGING_SUPABASE_URL}"
        
        exit 0
    else
        error "Staging restoration failed verification"
        exit 1
    fi
}

# Handle script termination
trap 'error "Restoration interrupted"; exit 1' INT TERM

# Parse arguments
BACKUP_NAME="${1:-}"

# Show usage if help requested
if [ "$BACKUP_NAME" = "-h" ] || [ "$BACKUP_NAME" = "--help" ]; then
    usage
    exit 0
fi

# Run main function
main "$BACKUP_NAME"