# Home Services Lead Generation - Makefile
# 
# Provides common development and deployment tasks

.PHONY: help install install-backend install-scraper setup test clean start dev db-init backend-deps backend-test backend-lint

# Default target
help:
	@echo "🏠 Home Services Lead Generation - Available Commands"
	@echo "=================================================="
	@echo "  make dev             - Run FastAPI backend in development mode with auto-reload"
	@echo "  make start           - Run backend in production mode"
	@echo "  make db-init         - Initialize database schema using apply_schema.py"
	@echo "  make install         - Install all Python dependencies"
	@echo "  make install-backend - Install backend dependencies only"
	@echo "  make install-scraper - Install permit_leads dependencies only"
	@echo "  make backend-deps    - Install backend Python dependencies"
	@echo "  make backend-test    - Run backend tests"
	@echo "  make backend-lint    - Run backend linting (if available)"
	@echo "  make redis-test      - Run Redis smoke test"
	@echo "  make setup           - Run full setup (same as install)"
	@echo "  make test            - Run tests"
	@echo "  make clean           - Clean Python cache files"
	@echo "  make help            - Show this help message"

# Development server with auto-reload
dev:
	@echo "Setting up development environment..."
	@# Copy .env.example to .env if .env doesn't exist in root directory
	@if [ ! -f .env ]; then \
		if [ ! -f .env.example ]; then \
			echo "❌ Error: .env.example not found in the root directory. Please add it before running 'make dev'."; \
			exit 1; \
		fi; \
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

# Production server
start:
	@echo "🚀 Starting backend in production mode..."
	cd backend && python main.py

# Initialize database schema
db-init:
	@echo "Initializing database schema..."
	cd backend && python scripts/apply_schema.py

# Initialize only billing tables (idempotent)
db-billing:
	@echo "Applying billing DDL..."
	cd backend && python scripts/apply_billing_schema.py

# Install all dependencies
install: install-scraper install-backend
	@echo "✅ All dependencies installed successfully!"

# Install backend dependencies
install-backend:
	@echo "📦 Installing backend dependencies..."
	pip install -r backend/requirements.txt

# Install backend dependencies (alias)
backend-deps:
	@echo "Installing backend dependencies..."
	cd backend && pip install -r requirements.txt

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

# Run backend tests
backend-test:
	@echo "Running backend tests..."
	cd backend && python -m pytest tests/ -v

# Run backend linting (placeholder for future linting setup)
backend-lint:
	@echo "Backend linting not configured yet."
	@echo "Consider adding flake8, black, or similar tools to requirements.txt"

# Clean Python cache files
clean:
	@echo "🧹 Cleaning Python cache files..."
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} + || true
	@echo "✅ Cleanup completed!"

# Redis smoke test
redis-test:
	@echo "🔴 Running Redis smoke test..."
	python scripts/redis_smoketest.py