import uuid

from sqlalchemy import func, select

from fast_kinda_solid_api.contexts import RequestContext
from fast_kinda_solid_api.database import Database
from fast_kinda_solid_api.observability.logs import logger


def get_session(database: Database):
    async def _get_session():
        logger.debug("Starting a new database session")
        async with database.session_maker() as session:
            async with session.begin():
                async with RequestContext.bind(session_id=str(uuid.uuid4())):
                    logger.debug("Session started")

                    transaction_id, connection_id = await _get_session_meta(session)
                    async with RequestContext.bind(
                        transaction_id=str(transaction_id), connection_id=str(connection_id)
                    ):
                        logger.debug("Session started")

                        try:
                            yield session
                        except Exception as e:
                            logger.error("An error occurred during the session. Rolling back.", exc_info=True)
                            await session.rollback()
                            raise e

                        logger.debug("Session closing")

    return _get_session


async def _get_session_meta(session):
    query = select(func.txid_current(), func.pg_backend_pid())
    result = await session.execute(query)
    row = result.one()
    return row.txid_current, row.pg_backend_pid


__all__ = [
    "get_session",
]
