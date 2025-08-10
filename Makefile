
# Home Services Lead Generation - Development Commands

.PHONY: dev install-backend help

# Default target
help:
	@echo "Available commands:"
	@echo "  make dev           - Run FastAPI backend in development mode with auto-reload"
	@echo "  make install-backend - Install backend dependencies"
	@echo "  make help          - Show this help message"

# Install backend dependencies
install-backend:
	@echo "Installing backend dependencies..."
	cd backend && pip install -r requirements.txt

# Development server with auto-reload
dev:
	@echo "Setting up development environment..."
	@# Copy .env.example to .env if .env doesn't exist in root directory
	@if [ ! -f .env ]; then \
		echo "Creating .env from .env.example..."; \
		cp .env.example .env; \
		echo "⚠️  Please edit .env and configure your environment variables"; \
	fi
	@echo "Starting FastAPI backend with auto-reload on port 8000..."
	@echo "📍 Healthcheck URL: http://localhost:8000/health"
	@echo "📍 API Documentation: http://localhost:8000/docs"
	@echo "📍 API Root: http://localhost:8000/"
	@echo ""
	cd backend && uvicorn main:app --host 0.0.0.0 --port 8000 --reload

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

# Automates common development tasks

.PHONY: help install install-backend install-scraper setup test clean

# Default target
help:
	@echo "🏠 Home Services Lead Generation - Available Commands"
	@echo "=================================================="
	@echo "make install         - Install all Python dependencies"
	@echo "make install-backend - Install backend dependencies only"
	@echo "make install-scraper - Install permit_leads dependencies only"
	@echo "make setup          - Run full setup (same as install)"
	@echo "make test           - Run tests"
	@echo "make clean          - Clean Python cache files"
	@echo "make help           - Show this help message"

# Install all dependencies
install: install-scraper install-backend
	@echo "✅ All dependencies installed successfully!"

# Install backend dependencies
install-backend:
	@echo "📦 Installing backend dependencies..."
	pip install -r backend/requirements.txt

# Install permit_leads/scraper dependencies
install-scraper:
	@echo "📦 Installing permit_leads dependencies..."
	python3 -m pip install -r backend/requirements.txt

# Install permit_leads/scraper dependencies
install-scraper:
	@echo "📦 Installing permit_leads dependencies..."
	python3 -m pip install -r permit_leads/requirements.txt

# Full setup (alias for install)
setup: install
	@echo ""
	@echo "🎉 Setup completed successfully!"
	@echo ""
	@echo "Next steps:"
	@echo "1. Configure environment variables:"
	@echo "   - Copy backend/.env.example to backend/.env"
	@echo "   - Copy frontend/.env.example to frontend/.env.local"
	@echo "2. Setup database (see README.md)"
	@echo "3. Install frontend dependencies: cd frontend && npm install"

# Run tests
test:
	@echo "🧪 Running tests..."
	cd permit_leads && python -m pytest tests/ || true
	cd backend && python -m pytest tests/ || true

# Clean Python cache files
clean:
	@echo "🧹 Cleaning Python cache files..."
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} + || true
	@echo "✅ Cleanup completed!"

