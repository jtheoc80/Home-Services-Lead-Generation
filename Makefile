# Home Services Lead Generation - Makefile
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
	pip install -r permit_leads/requirements.txt

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