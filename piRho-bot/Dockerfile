FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies (minimal - only what's needed for Python packages)
# gcc may be needed for some Python packages that compile C extensions
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean \
    && rm -rf /tmp/* /var/tmp/*

# Copy requirements first for better caching
# Use runtime requirements (without PyTorch) for smaller image
COPY requirements-runtime.txt .

# Install Python dependencies (PyTorch excluded for smaller image)
# PyTorch is optional - code handles missing torch gracefully
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements-runtime.txt && \
    pip cache purge

# Copy application code (training scripts and docs excluded via .dockerignore)
COPY . .

# Create directories for logs and cache
RUN mkdir -p /app/logs /app/news_cache /app/models

# Expose port (if needed for health checks)
EXPOSE 8080

# Health check - simple Python check
HEALTHCHECK --interval=60s --timeout=10s --start-period=120s --retries=3 \
    CMD python -c "import sys; sys.exit(0)" || exit 1

# Run the orchestrator
CMD ["python", "main.py", "--orchestrator"]

