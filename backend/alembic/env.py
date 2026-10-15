from logging.config import fileConfig

from sqlalchemy import create_engine, pool, text

from alembic import context
from app import models  # noqa: F401  (registers tables on Base.metadata)
from app.config import settings
from app.database import Base

config = context.config
if config.config_file_name:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata

# Two backend pods can start at the same time and both run `alembic upgrade head`.
# A Postgres advisory lock makes the second one wait instead of racing the first.
MIGRATION_LOCK_ID = 727_001


def run_migrations_offline() -> None:
    context.configure(url=settings.database_url, target_metadata=target_metadata, literal_binds=True)
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    engine = create_engine(settings.database_url, poolclass=pool.NullPool)
    with engine.connect() as connection:
        is_postgres = connection.dialect.name == "postgresql"
        if is_postgres:
            connection.execute(text("SELECT pg_advisory_lock(:id)"), {"id": MIGRATION_LOCK_ID})
            connection.commit()
        try:
            context.configure(connection=connection, target_metadata=target_metadata, compare_type=True)
            with context.begin_transaction():
                context.run_migrations()
        finally:
            if is_postgres:
                connection.execute(text("SELECT pg_advisory_unlock(:id)"), {"id": MIGRATION_LOCK_ID})
                connection.commit()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
