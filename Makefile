# LeadLedgerPro Makefile
# Environment management and deployment targets

.PHONY: help install install-backend install-frontend
.PHONY: dev dev-backend dev-frontend build build-backend build-frontend
.PHONY: test test-backend test-frontend lint
.PHONY: migrate seed stage-migrate stage-seed
.PHONY: clean clean-deps

# Default target
help:
	@echo "LeadLedgerPro Development Commands"
	@echo "=================================="
	@echo ""
	@echo "Setup:"
	@echo "  install          Install all dependencies"
	@echo "  install-backend  Install backend Python dependencies"
	@echo "  install-frontend Install frontend Node.js dependencies"
	@echo ""
	@echo "Development:"
	@echo "  dev              Start both backend and frontend in development mode"
	@echo "  dev-backend      Start backend development server"
	@echo "  dev-frontend     Start frontend development server"
	@echo ""
	@echo "Build:"
	@echo "  build            Build both backend and frontend for production"
	@echo "  build-backend    Build backend (prepare for deployment)"
	@echo "  build-frontend   Build frontend for production"
	@echo ""
	@echo "Testing:"
	@echo "  test             Run all tests"
	@echo "  test-backend     Run backend tests"
	@echo "  test-frontend    Run frontend tests"
	@echo "  lint             Run linters on all code"
	@echo ""
	@echo "Database:"
	@echo "  migrate          Run database migration (production)"
	@echo "  seed             Seed demo data (staging only)"
	@echo "  stage-migrate    Run database migration for staging environment"
	@echo "  stage-seed       Seed staging database with demo data"
	@echo ""
	@echo "Utilities:"
	@echo "  clean            Clean build artifacts"
	@echo "  clean-deps       Clean and reinstall all dependencies"

# Installation targets
install: install-backend install-frontend

install-backend:
	@echo "Installing backend dependencies..."
	cd backend && pip install -r requirements.txt

install-frontend:
	@echo "Installing frontend dependencies..."
	cd frontend && npm install

# Development targets
dev:
	@echo "Starting development servers..."
	@echo "Backend will be available at http://localhost:8000"
	@echo "Frontend will be available at http://localhost:3000"
	@echo "Press Ctrl+C to stop both servers"
	@echo ""
	@(trap 'kill 0' SIGINT; make dev-backend & make dev-frontend & wait)

dev-backend:
	@echo "Starting backend development server..."
	cd backend && python app.py

dev-frontend:
	@echo "Starting frontend development server..."
	cd frontend && npm run dev

# Build targets
build: build-backend build-frontend

build-backend:
	@echo "Building backend..."
	cd backend && python -m py_compile app.py
	cd backend && python -c "from app.settings import settings; print(f'✓ Backend configured for {settings.app_env} environment')"

build-frontend:
	@echo "Building frontend..."
	cd frontend && npm run build

# Testing targets
test: test-backend test-frontend

test-backend:
	@echo "Running backend tests..."
	cd backend && python -m pytest tests/ -v

test-frontend:
	@echo "Running frontend tests..."
	cd frontend && npm run lint

lint:
	@echo "Running linters..."
	@echo "Backend linting..."
	cd backend && python -m py_compile app.py
	cd backend && python -m py_compile app/settings.py
	cd backend && python -m py_compile app/health_api.py
	@echo "Frontend linting..."
	cd frontend && npm run lint

# Database targets
migrate:
	@echo "Running database migration..."
	python scripts/migrate.py

seed:
	@echo "Seeding demo data (staging environment only)..."
	@if [ "$(APP_ENV)" != "staging" ]; then \
		echo "❌ Error: Demo data seeding only allowed in staging environment."; \
		echo "Set APP_ENV=staging to continue."; \
		exit 1; \
	fi
	python scripts/seed_demo.py

stage-migrate:
	@echo "Running staging database migration..."
	APP_ENV=staging python scripts/migrate.py

stage-seed:
	@echo "Seeding staging database with demo data..."
	APP_ENV=staging python scripts/seed_demo.py --lead-count 200

# Health check targets
health:
	@echo "Checking application health..."
	@if curl -s http://localhost:8000/health > /dev/null 2>&1; then \
		echo "✓ Backend health check passed"; \
		curl -s http://localhost:8000/health | python -m json.tool; \
	else \
		echo "❌ Backend health check failed (is server running?)"; \
	fi

# Utility targets
clean:
	@echo "Cleaning build artifacts..."
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	find . -type f -name "*.pyo" -delete 2>/dev/null || true
	cd frontend && rm -rf .next 2>/dev/null || true
	cd frontend && rm -rf dist 2>/dev/null || true

clean-deps:
	@echo "Cleaning and reinstalling dependencies..."
	cd frontend && rm -rf node_modules package-lock.json
	make install

# Environment validation
validate-env:
	@echo "Validating environment configuration..."
	@python -c "from backend.app.settings import settings; print(f'Environment: {settings.app_env}'); print(f'Debug: {settings.debug}')"
	@if [ -f "backend/.env" ]; then echo "✓ Backend .env file exists"; else echo "⚠ Backend .env file missing"; fi
	@if [ -f "frontend/.env.local" ]; then echo "✓ Frontend .env.local file exists"; else echo "⚠ Frontend .env.local file missing"; fi

# Staging environment helpers
staging-setup:
	@echo "Setting up staging environment..."
	@echo "Creating staging environment files..."
	@if [ ! -f "backend/.env" ]; then cp backend/.env.example backend/.env; fi
	@if [ ! -f "frontend/.env.local" ]; then cp frontend/.env.example frontend/.env.local; fi
	@echo "Installing dependencies..."
	make install
	@echo "✓ Staging environment setup complete"
	@echo ""
	@echo "Next steps:"
	@echo "1. Configure staging environment variables in .env files"
	@echo "2. Run 'make stage-migrate' to set up database"
	@echo "3. Run 'make stage-seed' to add demo data"
	@echo "4. Run 'make dev' to start development servers"

# Production deployment helpers
prod-deploy:
	@echo "Production deployment steps:"
	@echo "1. Set APP_ENV=production"
	@echo "2. Configure production environment variables"
	@echo "3. Run 'make build' to build applications"
	@echo "4. Run 'make migrate' to update database schema"
	@echo "5. Deploy built applications to production infrastructure"