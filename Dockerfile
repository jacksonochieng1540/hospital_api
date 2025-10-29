# Multi-stage Dockerfile for Hospital API

# Stage 1: Builder stage
FROM python:3.11-slim as builder

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Create and activate virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy and install Python dependencies
COPY requirements.txt .
RUN pip install --upgrade pip setuptools wheel && \
    pip install -r requirements.txt && \
    pip install gunicorn psycopg2-binary whitenoise

# Stage 2: Runtime stage
FROM python:3.11-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/opt/venv/bin:$PATH" \
    DJANGO_SETTINGS_MODULE=hospital_project.settings

# Install runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    postgresql-client \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv

# Create app user and directories
RUN useradd -m -u 1000 appuser && \
    mkdir -p /app/static /app/media /app/logs && \
    chown -R appuser:appuser /app

# Set work directory
WORKDIR /app

# Copy project files
COPY --chown=appuser:appuser . .

# Create startup script
RUN echo '#!/bin/bash\n\
set -e\n\
\n\
echo "Waiting for PostgreSQL..."\n\
while ! pg_isready -h "${DB_HOST:-db}" -p "${DB_PORT:-5432}" -U "${DB_USER:-postgres}" > /dev/null 2>&1; do\n\
  sleep 1\n\
done\n\
echo "PostgreSQL started"\n\
\n\
echo "Running migrations..."\n\
python manage.py migrate --noinput\n\
\n\
echo "Collecting static files..."\n\
python manage.py collectstatic --noinput\n\
\n\
echo "Starting Gunicorn..."\n\
exec gunicorn hospital_project.wsgi:application \\\n\
    --bind 0.0.0.0:${PORT:-8000} \\\n\
    --workers ${GUNICORN_WORKERS:-4} \\\n\
    --threads ${GUNICORN_THREADS:-2} \\\n\
    --timeout ${GUNICORN_TIMEOUT:-120} \\\n\
    --worker-class sync \\\n\
    --max-requests 1000 \\\n\
    --max-requests-jitter 50 \\\n\
    --access-logfile - \\\n\
    --error-logfile - \\\n\
    --log-level info\n\
' > /app/entrypoint.sh && chmod +x /app/entrypoint.sh

# Switch to app user
USER appuser

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:${PORT:-8000}/api/ || exit 1

# Set entrypoint
ENTRYPOINT ["/app/entrypoint.sh"]