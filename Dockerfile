# Multi-stage build for PineScript RAG Server
FROM python:3.11-slim as builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# Production stage
FROM python:3.11-slim

WORKDIR /app

# Copy installed packages from builder
# Copy installed packages from builder
COPY --from=builder /root/.local /root/.local

# Copy application code
COPY . /app
# Add local bin to PATH
ENV PATH=/root/.local/bin:$PATH

# Expose port
EXPOSE 8000

# Health check - keep lightweight and optional
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD ["/bin/sh", "-c", "curl -f http://localhost:8000/status || exit 1"]

# Allow configuring Gunicorn args via env (e.g. --timeout)
# Default: 3 minute timeout and a short graceful timeout
ENV GUNICORN_CMD_ARGS="--timeout 180 --graceful-timeout 60"

# Run application with Uvicorn in production mode. Use `$GUNICORN_CMD_ARGS` so
# runtime overrides are easy (docker run -e GUNICORN_CMD_ARGS="..." ...).
CMD ["sh", "-c", "gunicorn -k uvicorn.workers.UvicornWorker -w 4 -b 0.0.0.0:8000 server.app:app $GUNICORN_CMD_ARGS --log-level info"]
