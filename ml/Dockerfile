# =============================================================================
# PEA RE Forecast Platform - ML Service Dockerfile
# Multi-stage build with non-root user for security
# =============================================================================

# Build stage
FROM python:3.11-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir --user -r requirements.txt

# Production stage
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app
ENV PATH="/home/mluser/.local/bin:$PATH"

WORKDIR /app

# Install runtime dependencies only
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user for security
RUN groupadd --gid 1000 mluser && \
    useradd --uid 1000 --gid mluser --shell /bin/bash --create-home mluser

# Copy Python packages from builder
COPY --from=builder /root/.local /home/mluser/.local

# Copy application code
COPY --chown=mluser:mluser . .

# Create model directory with proper ownership
RUN mkdir -p /app/models && chown -R mluser:mluser /app/models

# Switch to non-root user
USER mluser

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8001/health || exit 1

# Expose port
EXPOSE 8001

# Run ML service
CMD ["uvicorn", "src.api:app", "--host", "0.0.0.0", "--port", "8001"]
