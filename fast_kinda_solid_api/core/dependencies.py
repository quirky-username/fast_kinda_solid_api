import uuid

from fastapi.concurrency import asynccontextmanager
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from structlog import getLogger

from fast_kinda_solid_api.core.observability.context import RequestContext

logger = getLogger(__name__)


@asynccontextmanager
async def get_async_session(async_session: async_sessionmaker[AsyncSession]):
    logger.debug("Starting a new database session")

    async with async_session() as session:
        async with session.begin():
            async with RequestContext.bind(session_id=str(uuid.uuid4())):
                logger.debug("Session started")

                transaction_id, connection_id = await _get_session_meta(session)
                async with RequestContext.bind(transaction_id=str(transaction_id), connection_id=str(connection_id)):
                    logger.debug("Session started")

                    try:
                        yield session
                    except Exception as e:
                        logger.error("An error occurred during the session. Rolling back.", exc_info=True)
                        await session.rollback()
                        raise e

                    logger.debug("Session closing")


async def _get_session_meta(session):
    query = select(func.txid_current(), func.pg_backend_pid())
    result = await session.execute(query)
    row = result.one()
    return row.txid_current, row.pg_backend_pid


__all__ = [
    "get_async_session",
]
