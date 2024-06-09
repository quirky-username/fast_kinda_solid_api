import uuid

import pytest
from fastapi import HTTPException
from fastapi.responses import JSONResponse
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text

from fast_kinda_solid_api.config import ServerSettings
from fast_kinda_solid_api.server import BaseAPIServer
from tests.fixtures.db import database


@pytest.fixture(scope="session")
def setup_test_db():
    admin_db_url = database.settings.get_sync_url(database.settings.ADMIN_DB)
    db_url = database.settings.get_sync_url(database.settings.DB)

    admin_engine = create_engine(admin_db_url, isolation_level="AUTOCOMMIT")
    db_engine = create_engine(db_url, isolation_level="AUTOCOMMIT")

    # setup database
    with admin_engine.connect() as connection:
        connection.execute(text(f'DROP DATABASE IF EXISTS "{database.settings.DB}"'))
        connection.execute(text(f'CREATE DATABASE "{database.settings.DB}"'))

    # create tables
    database.import_models()
    database.registry.metadata.create_all(db_engine)

    yield database

    # force cleanup all connections to the db
    # this comes from the connection pool
    db_engine.dispose()
    with admin_engine.connect() as connection:
        connection.execute(
            text(
                f"""SELECT pg_terminate_backend(pg_stat_activity.pid)
            FROM pg_stat_activity
            WHERE pg_stat_activity.datname = '{database.settings.DB}'
            AND pid <> pg_backend_pid();"""
            )
        )

    # tear down database
    with admin_engine.connect() as connection:
        connection.execute(text(f'DROP DATABASE IF EXISTS "{database.settings.DB}"'))


@pytest.fixture(scope="module")
def base_api_server() -> BaseAPIServer:
    app = BaseAPIServer(name=f"test_server_{uuid.uuid4()}", settings=ServerSettings())

    @app.get("/raise-exception")
    async def raise_exception():
        raise Exception("Test Exception")

    @app.get("/not-found")
    async def not_found():
        raise HTTPException(status_code=404, detail="Not Found")

    @app.get("/foo")
    async def bar():
        return JSONResponse({"value": "bar"})

    return app


@pytest.fixture(scope="function")
def test_client(base_api_server) -> TestClient:
    return TestClient(base_api_server)
