FROM python:3.11-slim

WORKDIR /app

# Install system dependencies for psycopg
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy dependency files
COPY pyproject.toml ./

# Copy application code
COPY app/ ./app/
COPY alembic/ ./alembic/
COPY alembic.ini ./

# Install dependencies (default: SQLite only, override with INSTALL_SPEC build arg)
ARG INSTALL_SPEC=.
RUN pip install --no-cache-dir "$INSTALL_SPEC"

# Copy entrypoint script
COPY docker-entrypoint.sh ./
RUN chmod +x docker-entrypoint.sh

EXPOSE 9000

ENTRYPOINT ["./docker-entrypoint.sh"]
CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "9000"]
