import logging
import re
from contextvars import ContextVar

import pytest
import structlog

from fast_kinda_solid_api.core.observability.context import BaseObservabilityContext
from fast_kinda_solid_api.core.observability.logs import configure_logging
from fast_kinda_solid_api.core.settings import LogLevel, ObservabilitySettings


def strip_ansi_codes(text):
    ansi_escape = re.compile(r"\x1B[@-_][0-?]*[ -/]*[@-~]")
    return ansi_escape.sub("", text)


@pytest.fixture
def console_logging_settings():
    configure_logging(ObservabilitySettings(CONSOLE_LOGGING=True, LOG_LEVEL=LogLevel.DEBUG))
    yield
    logging.shutdown()


@pytest.fixture
def json_logging_settings():
    configure_logging(ObservabilitySettings(CONSOLE_LOGGING=False, LOG_LEVEL=LogLevel.DEBUG))
    yield
    logging.shutdown()


class ContextThing(BaseObservabilityContext):
    id: ContextVar[str] = ContextVar("observability.context_thing.id")
    name: ContextVar[str] = ContextVar("observability.context_thing.name")


@pytest.fixture
def setup_context():
    ContextThing.id.set(1)
    ContextThing.name.set("Test")


def test_console_logging_format(console_logging_settings, setup_context, caplog):
    logger = structlog.get_logger()
    with caplog.at_level(logging.INFO):
        logger.info("Hello, world!")

    assert len(caplog.records) == 1
    log_record = caplog.records[0]
    message = strip_ansi_codes(log_record.message)
    assert "Hello, world!" in message
    assert "context_thing.id=1" in message
    assert "context_thing.name=Test" in message


def test_json_logging_format(json_logging_settings, setup_context, caplog):
    logger = structlog.get_logger()
    with caplog.at_level(logging.INFO):
        logger.info("Hello, world!")

    assert len(caplog.records) == 1
    log_record = caplog.records[0]
    log_message = log_record.getMessage()
    assert "Hello, world!" in log_message
    assert '"context_thing.id": 1' in log_message
    assert '"context_thing.name": "Test"' in log_message


def test_log_level_filtering_console(console_logging_settings, caplog):
    logger = structlog.get_logger()
    with caplog.at_level(logging.WARNING):
        logger.info("This should not appear")
        logger.warning("This should appear")

    assert len(caplog.records) == 1
    assert "This should appear" in caplog.records[0].message


def test_log_level_filtering_json(json_logging_settings, caplog):
    logger = structlog.get_logger()
    with caplog.at_level(logging.WARNING):
        logger.info("This should not appear")
        logger.warning("This should appear")

    assert len(caplog.records) == 1
    assert "This should appear" in caplog.records[0].message


def test_context_variable_inclusion(console_logging_settings, setup_context, caplog):
    logger = structlog.get_logger()
    with caplog.at_level(logging.INFO):
        logger.info("Test context variables")

    assert len(caplog.records) == 1
    log_record = caplog.records[0]
    message = strip_ansi_codes(log_record.message)
    assert "context_thing.id=1" in message
    assert "context_thing.name=Test" in message


def test_context_variable_inclusion_json(json_logging_settings, setup_context, caplog):
    logger = structlog.get_logger()
    with caplog.at_level(logging.INFO):
        logger.info("Test context variables")

    assert len(caplog.records) == 1
    log_record = caplog.records[0]
    log_message = log_record.getMessage()
    assert '"context_thing.id": 1' in log_message
    assert '"context_thing.name": "Test"' in log_message
