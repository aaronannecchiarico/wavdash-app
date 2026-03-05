# Use Python 3.11 slim image
FROM python:3.11-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies
# curl is required by the HEALTHCHECK command
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    ffmpeg \
    libsndfile1 \
    libsndfile1-dev \
    git \
    && rm -rf /var/lib/apt/lists/*

# Create app user
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Create and set work directory
WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.txt .
COPY scripts/install.py scripts/install.py

# Install dependencies with optional GPU support
# Use build arg to enable GPU support: --build-arg ENABLE_GPU=true
ARG ENABLE_GPU=false
RUN if [ "$ENABLE_GPU" = "true" ]; then \
        python scripts/install.py --gpu; \
    else \
        pip install --no-cache-dir -r requirements.txt; \
    fi

# Create necessary directories
RUN mkdir -p /app/logs /app/outputs /tmp/audio_processing \
    && chown -R appuser:appuser /app /tmp/audio_processing

# Copy application code
COPY . .

# Change ownership of app directory
RUN chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Default command (can be overridden)
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]