import os
from sqlalchemy import engine_from_config, pool
from alembic import context
from logging.config import fileConfig
from database import Base
import models  # import all models

config = context.config

# Use environment variable if set
DATABASE_URL = os.getenv("DATABASE_URL", config.get_main_option("sqlalchemy.url"))

fileConfig(config.config_file_name)
target_metadata = Base.metadata

def run_migrations_online():
    connectable = engine_from_config(
        {"sqlalchemy.url": DATABASE_URL},  # <- use dict here
        prefix='sqlalchemy.',
        poolclass=pool.NullPool
    )
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode():
    context.configure(url=DATABASE_URL, target_metadata=target_metadata, literal_binds=True)
    with context.begin_transaction():
        context.run_migrations()
else:
    run_migrations_online()