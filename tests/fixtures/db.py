from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import AsyncSession

from fast_kinda_solid_api.config import SqlAlchemySettings
from fast_kinda_solid_api.database import Database

database = Database(
    "test",
    SqlAlchemySettings(
        DB="test-adventurebee-api",
        ADMIN_DB="postgres",
        HOST="localhost",
        PORT=5432,
        USER="adventurebee-api",
        PASSWORD="SecurePasswasdford",
        ASYNC_DIALECT="postgresql",
        ASYNC_DRIVER="asyncpg",
        SYNC_DIALECT="postgresql",
        SYNC_DRIVER="psycopg2",
    ),
    models=["tests.fixtures.models"],
)


@asynccontextmanager
async def get_db_session(db: Database):
    async with db.async_engine.connect() as connection:
        async with connection.begin() as transaction:
            session = AsyncSession(bind=connection, join_transaction_mode="create_savepoint")
            yield session
            await transaction.rollback()
