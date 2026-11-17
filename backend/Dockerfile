# Backend Dockerfile for LBG Clear Path
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies for psycopg
RUN apt-get update && \
    apt-get install -y --no-install-recommends libpq-dev gcc && \
    rm -rf /var/lib/apt/lists/*

# Copy dependency files
COPY pyproject.toml ./
COPY alembic.ini ./

# Copy application code
COPY app/ ./app/
COPY alembic/ ./alembic/

# Install dependencies (default to base dependencies only)
ARG INSTALL_SPEC=.
RUN pip install --no-cache-dir "$INSTALL_SPEC"

# Copy and set entrypoint for migrations and seeding
COPY docker-entrypoint.sh ./
RUN chmod +x docker-entrypoint.sh

EXPOSE 8000

ENTRYPOINT ["./docker-entrypoint.sh"]
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
