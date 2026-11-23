# Backend Dockerfile (multi-stage)
FROM python:3.11-slim AS install

WORKDIR /app

# Install system dependencies for Python packages
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy dependency files
COPY backend/pyproject.toml ./

# Install dependencies (support optional extras via build arg)
ARG PIP_TARGET=.
RUN pip install --no-cache-dir "$PIP_TARGET"

# Runtime stage
FROM python:3.11-slim AS runtime

WORKDIR /app

# Copy installed packages from install stage
COPY --from=install /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=install /usr/local/bin /usr/local/bin

# Copy application code
COPY backend/app ./app
COPY backend/alembic.ini ./
COPY backend/alembic ./alembic
COPY backend/docker-entrypoint.sh ./

# Make entrypoint executable
RUN chmod +x ./docker-entrypoint.sh

# Environment variables
ARG BACKEND_HOST=backend
ENV BACKEND_HOST=${BACKEND_HOST}
ENV PYTHONUNBUFFERED=1

# Expose backend port
EXPOSE 9000

# Run migrations on startup, then start server
ENTRYPOINT ["sh", "./docker-entrypoint.sh"]
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "9000"]
