"""Alembic environment configuration."""
import os
from logging.config import fileConfig

from sqlalchemy import create_engine, pool

from alembic import context

# Import Base and all models to ensure they're registered
from app.core.db import Base
import app.models.users  # noqa: F401
import app.models.roles  # noqa: F401
import app.models.sessions  # noqa: F401
import app.models.customers  # noqa: F401
import app.models.receivables  # noqa: F401
import app.models.queue  # noqa: F401
import app.models.promises  # noqa: F401
import app.models.policy  # noqa: F401
import app.models.audit  # noqa: F401

# Alembic Config object
config = context.config

# Interpret the config file for Python logging
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Target metadata for autogenerate
target_metadata = Base.metadata

# Get database URL from environment or use default
database_url = os.getenv("DATABASE_URL", "sqlite:///./app.db")
config.set_main_option("sqlalchemy.url", database_url)


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        render_as_batch=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    connectable = create_engine(
        config.get_main_option("sqlalchemy.url"),
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            render_as_batch=True,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
