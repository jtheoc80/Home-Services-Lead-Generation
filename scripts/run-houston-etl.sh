#!/bin/bash

# Houston ETL and Lead Generation Runner
# Implementation of the problem statement requirements

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
DRY_RUN=false
VERBOSE=false

# Parse command line arguments
while [[ $# -gt 0 ]]; do
  case $1 in
    --dry-run)
      DRY_RUN=true
      shift
      ;;
    --verbose|-v)
      VERBOSE=true
      shift
      ;;
    --help|-h)
      echo "Usage: $0 [options]"
      echo "Options:"
      echo "  --dry-run     Show what would be done without executing"
      echo "  --verbose, -v Show verbose output"
      echo "  --help, -h    Show this help message"
      echo ""
      echo "Environment variables:"
      echo "  SUPABASE_URL              - Supabase project URL (required)"
      echo "  SUPABASE_SERVICE_ROLE_KEY - Supabase service role key (required)"
      echo "  HOUSTON_WEEKLY_XLSX_URL   - Houston weekly permits URL"
      echo "  HOUSTON_SOLD_PERMITS_URL  - Houston sold permits URL"
      exit 0
      ;;
    *)
      echo "Unknown option $1"
      exit 1
      ;;
  esac
done

# Functions
log() {
  echo -e "${BLUE}[$(date '+%Y-%m-%d %H:%M:%S')]${NC} $1"
}

success() {
  echo -e "${GREEN}✅${NC} $1"
}

warning() {
  echo -e "${YELLOW}⚠️${NC} $1"
}

error() {
  echo -e "${RED}❌${NC} $1"
}

check_requirements() {
  log "Checking requirements..."
  
  # Check for required environment variables
  local missing_vars=()
  
  if [[ -z "${SUPABASE_URL:-}" ]]; then
    missing_vars+=("SUPABASE_URL")
  fi
  
  if [[ -z "${SUPABASE_SERVICE_ROLE_KEY:-}" ]]; then
    missing_vars+=("SUPABASE_SERVICE_ROLE_KEY")
  fi
  
  if [[ ${#missing_vars[@]} -gt 0 ]]; then
    error "Missing required environment variables: ${missing_vars[*]}"
    echo "Please set these variables before running the script."
    exit 1
  fi
  
  # Check for Node.js and required commands
  if ! command -v node &> /dev/null; then
    error "Node.js is not installed or not in PATH"
    exit 1
  fi
  
  if ! command -v npm &> /dev/null; then
    error "npm is not installed or not in PATH"
    exit 1
  fi
  
  success "All requirements satisfied"
}

trigger_github_workflow() {
  log "Triggering Houston ETL workflow on GitHub Actions..."
  
  if [[ "$DRY_RUN" == "true" ]]; then
    warning "[DRY RUN] Would trigger workflow: etl-houston-ondemand.yml"
    return 0
  fi
  
  # Check if gh CLI is available
  if command -v gh &> /dev/null; then
    if gh workflow run .github/workflows/etl-houston-ondemand.yml --field days=14; then
      success "GitHub workflow triggered successfully"
      warning "Note: Workflow will run on self-hosted runner with [self-hosted, linux, x64, scrape] tags"
    else
      warning "Failed to trigger GitHub workflow, will run ETL locally instead"
      return 1
    fi
  else
    warning "GitHub CLI (gh) not available, running ETL locally instead"
    return 1
  fi
}

run_etl_locally() {
  log "Running Houston ETL locally..."
  
  if [[ "$DRY_RUN" == "true" ]]; then
    warning "[DRY RUN] Would run: npm run ingest:coh"
    return 0
  fi
  
  if npm run ingest:coh; then
    success "Houston ETL completed locally"
  else
    error "Houston ETL failed"
    return 1
  fi
}

run_typescript_script() {
  log "Running comprehensive TypeScript ETL and lead generation script..."
  
  local cmd="npm run houston:etl-and-mint"
  if [[ "$DRY_RUN" == "true" ]]; then
    cmd="npm run houston:etl-and-mint:dry-run"
  fi
  
  if [[ "$VERBOSE" == "true" ]]; then
    log "Command: $cmd"
  fi
  
  if $cmd; then
    success "TypeScript script completed successfully"
  else
    error "TypeScript script failed"
    return 1
  fi
}

show_sql_instructions() {
  echo ""
  log "To execute the SQL commands manually in Supabase:"
  echo ""
  echo "1. Open your Supabase dashboard"
  echo "2. Go to SQL Editor"
  echo "3. Execute the following SQL file:"
  echo "   sql/houston-etl-mint-leads.sql"
  echo ""
  echo "Or execute these individual queries:"
  echo ""
  echo "-- Check permits from last 7 days"
  echo "SELECT count(*) FROM public.permits WHERE issued_date >= now() - interval '7 days';"
  echo ""
  echo "-- Mint leads (limit 50, last 365 days)"
  echo "SELECT public.upsert_leads_from_permits_limit(50,365);"
  echo ""
  echo "-- Check latest leads"
  echo "SELECT source, external_permit_id, name, county, trade, address, zipcode, created_at"
  echo "FROM public.leads ORDER BY created_at DESC LIMIT 50;"
  echo ""
}

main() {
  echo "🚀 Houston ETL and Lead Generation Pipeline"
  echo "============================================"
  echo ""
  
  if [[ "$DRY_RUN" == "true" ]]; then
    warning "DRY RUN MODE - No actual changes will be made"
    echo ""
  fi
  
  check_requirements
  
  # Try to trigger GitHub workflow first, fall back to local execution
  if ! trigger_github_workflow; then
    run_etl_locally
  fi
  
  # Run the comprehensive TypeScript script
  run_typescript_script
  
  # Show SQL instructions for manual execution
  show_sql_instructions
  
  success "Pipeline completed!"
  
  # Show summary file location
  if [[ -f "logs/houston-etl-mint-leads-summary.json" ]]; then
    log "Summary written to: logs/houston-etl-mint-leads-summary.json"
  fi
}

# Execute main function
main "$@"