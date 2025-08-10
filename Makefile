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