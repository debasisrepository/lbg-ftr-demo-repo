# Backend Dockerfile - Multi-stage build for production
FROM python:3.11-slim AS install

WORKDIR /app

# Install system dependencies for Python packages
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy package files
COPY pyproject.toml ./

# Copy the app package directory (required for pip install .)
COPY app/ ./app/

# Install Python dependencies
ARG INSTALL_SPEC=.
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir "$INSTALL_SPEC"

# Runtime stage
FROM python:3.11-slim

WORKDIR /app

# Install runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    && rm -rf /var/lib/apt/lists/*

# Copy installed packages from install stage
COPY --from=install /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=install /usr/local/bin /usr/local/bin

# Copy application code
COPY app/ ./app/
COPY alembic/ ./alembic/
COPY alembic.ini ./

# Copy entrypoint script
COPY docker-entrypoint.sh ./
RUN chmod +x ./docker-entrypoint.sh

# Expose the backend port
EXPOSE 8000

# Set entrypoint to run migrations and start the app
ENTRYPOINT ["./docker-entrypoint.sh"]
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
