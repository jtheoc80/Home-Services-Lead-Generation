#!/bin/bash
"""
Nightly training script runner.

This script sets up the environment and runs the ML training pipeline.
Designed to be run as a cron job or scheduled task.
"""

set -e  # Exit on any error

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$(dirname "$SCRIPT_DIR")"
PROJECT_ROOT="$(dirname "$BACKEND_DIR")"

# Load environment variables
if [ -f "$PROJECT_ROOT/frontend/.env" ]; then
    source "$PROJECT_ROOT/frontend/.env"
elif [ -f "$PROJECT_ROOT/.env" ]; then
    source "$PROJECT_ROOT/.env"
fi

# Check if training is enabled
if [ "$ENABLE_NIGHTLY_TRAINING" != "true" ]; then
    echo "Nightly training is disabled. Set ENABLE_NIGHTLY_TRAINING=true to enable."
    exit 0
fi

# Validate required environment variables
if [ -z "$DATABASE_URL" ]; then
    echo "ERROR: DATABASE_URL environment variable is required"
    exit 1
fi

# Set defaults
MODEL_DIR="${MODEL_DIR:-$BACKEND_DIR/models}"
LOG_DIR="${LOG_DIR:-$BACKEND_DIR/logs}"

# Create directories if they don't exist
mkdir -p "$MODEL_DIR"
mkdir -p "$LOG_DIR"

# Log file with timestamp
LOG_FILE="$LOG_DIR/training_$(date +%Y%m%d_%H%M%S).log"

echo "Starting nightly ML training pipeline..."
echo "Log file: $LOG_FILE"
echo "Model directory: $MODEL_DIR"

# Run training with logging
cd "$BACKEND_DIR"
python3 -m pip install -r requirements.txt >> "$LOG_FILE" 2>&1

# Set environment variables for Python script
export MODEL_DIR="$MODEL_DIR"
export DATABASE_URL="$DATABASE_URL"

# Run training
python3 app/train_model.py >> "$LOG_FILE" 2>&1

# Check exit code
TRAINING_EXIT_CODE=$?

if [ $TRAINING_EXIT_CODE -eq 0 ]; then
    echo "Training completed successfully"
    
    # Optional: Clean up old log files (keep last 7 days)
    find "$LOG_DIR" -name "training_*.log" -mtime +7 -delete
    
    # Optional: Clean up old model files (keep last 5 versions)
    find "$MODEL_DIR" -name "lead_model_*.pkl" -type f | sort -r | tail -n +6 | xargs rm -f
    
else
    echo "Training failed with exit code $TRAINING_EXIT_CODE"
    echo "Check log file: $LOG_FILE"
    exit $TRAINING_EXIT_CODE
fi

echo "Nightly training completed"