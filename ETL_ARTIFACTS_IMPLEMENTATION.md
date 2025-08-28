# ETL Artifacts and Diagnostics Implementation Summary

## Overview

This implementation adds deterministic artifacts handling, better diagnostics, and graceful empty exit conditions to the ETL pipeline as requested in the problem statement.

## Changes Made

### 1. Created `scripts/ensure_artifacts.py`

A new script that:
- ✅ Creates `logs/` and `artifacts/` directories if missing
- ✅ Ensures `logs/etl_output.log` exists (creates if missing) 
- ✅ Handles `ETL_ALLOW_EMPTY="1"` environment variable to make process exit code 0 instead of 1 when pipeline found 0 records (downshift a known-empty condition)

### 2. Enhanced `scripts/etlDelta.ts` (Main ETL Runner)

Added the following behaviors:
- ✅ Print current working directory and list of discovered CSVs before processing (glob for `data/**/*.csv` recursively)
- ✅ Write a summary line to `logs/etl_output.log` with the record count
- ✅ On "no input found" treat as a handled condition when `ETL_ALLOW_EMPTY=1`
- ✅ At the end of the ETL script, call `scripts/ensure_artifacts.py`

### 3. Enhanced `permit_leads/main.py` (Alternative ETL Runner)

Added the following behaviors:
- ✅ Print current working directory and list of discovered CSVs before processing
- ✅ Save any generated CSVs into `artifacts/` directory (not repo root)
- ✅ Write summary lines to `logs/etl_output.log` with record counts
- ✅ On "no input found" treat as a handled condition when `ETL_ALLOW_EMPTY=1`
- ✅ At the end of the ETL script, call `scripts/ensure_artifacts.py`

## Key Features

### Deterministic Artifacts
- CSV files are now saved to `artifacts/` directory instead of the repository root
- Consistent directory structure created by `ensure_artifacts.py`
- Log files stored in `logs/` directory

### Better Diagnostics
- Current working directory printed at start of ETL runs
- CSV file discovery shows all `data/**/*.csv` files found
- Summary logging to `logs/etl_output.log` with timestamps and record counts
- Detailed console output for debugging

### Graceful Empty Exit
- When `ETL_ALLOW_EMPTY=1` environment variable is set:
  - Process exits with code 0 instead of 1 when no records found
  - Calls `ensure_artifacts.py --empty-pipeline` for proper handling
  - Logs the empty condition as a handled state

## Usage Examples

### TypeScript ETL (Harris County)
```bash
# Normal operation
tsx scripts/etlDelta.ts

# With graceful empty handling
ETL_ALLOW_EMPTY=1 tsx scripts/etlDelta.ts
```

### Python ETL (General Permits)
```bash
# Normal operation  
python -m permit_leads scrape --jurisdiction tx-harris

# With graceful empty handling
ETL_ALLOW_EMPTY=1 python -m permit_leads scrape --jurisdiction tx-harris
```

### Manual Artifacts Management
```bash
# Ensure directories and log file exist
python3 scripts/ensure_artifacts.py

# Handle empty pipeline condition
ETL_ALLOW_EMPTY=1 python3 scripts/ensure_artifacts.py --empty-pipeline
```

## Files Modified/Created

### Created
- `scripts/ensure_artifacts.py` - New script for artifacts and directory management

### Modified
- `scripts/etlDelta.ts` - Enhanced with diagnostics and artifacts handling
- `permit_leads/main.py` - Enhanced with diagnostics and artifacts handling

## Testing Verification

All functionality has been tested:
- ✅ Directory creation (`logs/`, `artifacts/`)
- ✅ Log file creation and writing
- ✅ CSV file discovery
- ✅ Environment variable handling (`ETL_ALLOW_EMPTY=1`)
- ✅ Script execution and integration
- ✅ Error handling and graceful exits

## Environment Variables

- `ETL_ALLOW_EMPTY=1` - Set to enable graceful exit (code 0) when no records found
- Existing ETL environment variables remain unchanged

This implementation provides deterministic artifacts, better diagnostics, and graceful empty exit handling as requested, while maintaining backward compatibility with existing ETL workflows.