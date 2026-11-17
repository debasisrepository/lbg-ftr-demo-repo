"""Alembic migration environment."""
import os
from logging.config import fileConfig

from alembic import context
from sqlalchemy import create_engine

# Import all models to ensure they're registered with Base
from app.database import Base
import app.models.auth  # noqa: F401
import app.models.case  # noqa: F401
import app.models.ownership  # noqa: F401
import app.models.continuity  # noqa: F401
import app.models.communication  # noqa: F401
import app.models.actions  # noqa: F401
import app.models.incident  # noqa: F401
import app.models.config  # noqa: F401
import app.models.governance  # noqa: F401
import app.models.audit  # noqa: F401

# this is the Alembic Config object
config = context.config

# Interpret the config file for Python logging
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Read DATABASE_URL from environment
database_url = os.getenv("DATABASE_URL", "sqlite:///./app.db")
config.set_main_option("sqlalchemy.url", database_url)

target_metadata = Base.metadata


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
    connectable = create_engine(config.get_main_option("sqlalchemy.url"))

    with connectable.connect() as connection:
        context.configure(
            connection=connection, target_metadata=target_metadata, render_as_batch=True
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
