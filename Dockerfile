# Multi-stage Dockerfile for Dozentenmanager Flask Application
# Stage 1: Build stage with UV for fast dependency installation
FROM python:3.12-slim AS builder

# Install system dependencies required for building Python packages
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Install UV package manager
RUN pip install --no-cache-dir uv

# Set working directory
WORKDIR /app

# Copy dependency files
COPY pyproject.toml ./

# Create virtual environment and install dependencies using UV
RUN uv venv /app/.venv --seed
ENV PATH="/app/.venv/bin:$PATH"
RUN uv pip install -e .

# Stage 2: Runtime stage
FROM python:3.12-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/app/.venv/bin:$PATH" \
    FLASK_APP=run.py

# Create non-root user for security
RUN useradd -m -u 1000 appuser && \
    mkdir -p /app /app/instance /app/uploads && \
    chown -R appuser:appuser /app

# Set working directory
WORKDIR /app

# Copy virtual environment from builder stage
COPY --from=builder --chown=appuser:appuser /app/.venv /app/.venv

# Copy application code
COPY --chown=appuser:appuser . .

# Switch to non-root user
USER appuser

# Create necessary directories with proper permissions
RUN mkdir -p instance uploads logs migrations/versions

# Expose port
EXPOSE 5000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:5000/', timeout=5)" || exit 1

# Default command (can be overridden)
CMD ["python", "run.py"]
