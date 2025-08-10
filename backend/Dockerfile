# Production-ready Dockerfile for Python FastAPI backend
# Base image: Python 3.11 slim for optimal performance and security
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Set environment variables for Python optimization
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    APP_MODULE="backend.main:app" \
    PORT=8000

# Install system dependencies required for Python packages
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy and install Python dependencies first for better Docker layer caching
# This allows dependency layer to be cached when only source code changes
COPY backend/requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy backend source code
COPY backend/ .

# Create non-root user for security best practices
RUN adduser --disabled-password --gecos '' appuser && \
    chown -R appuser:appuser /app
USER appuser

# Expose port 8000 for the FastAPI application
EXPOSE 8000

# Use Gunicorn with UvicornWorker for production deployment
# Configure with specified timeout and worker count for optimal performance
CMD ["sh", "-c", "gunicorn -k uvicorn.workers.UvicornWorker ${APP_MODULE} --bind 0.0.0.0:${PORT:-8000} --timeout 120 --workers 2"]