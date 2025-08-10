# Home Services Lead Generation - Makefile
# 
# Provides common development and deployment tasks

.PHONY: help db-init backend-deps backend-test backend-lint

# Default target
help:
	@echo "Available targets:"
	@echo "  db-init       - Initialize database schema using apply_schema.py"
	@echo "  backend-deps  - Install backend Python dependencies"
	@echo "  backend-test  - Run backend tests"
	@echo "  backend-lint  - Run backend linting (if available)"
	@echo "  help          - Show this help message"

# Initialize database schema
db-init:
	@echo "Initializing database schema..."
	cd backend && python scripts/apply_schema.py

# Install backend dependencies
backend-deps:
	@echo "Installing backend dependencies..."
	cd backend && pip install -r requirements.txt

# Run backend tests
backend-test:
	@echo "Running backend tests..."
	cd backend && python -m pytest tests/ -v

# Run backend linting (placeholder for future linting setup)
backend-lint:
	@echo "Backend linting not configured yet."
	@echo "Consider adding flake8, black, or similar tools to requirements.txt"