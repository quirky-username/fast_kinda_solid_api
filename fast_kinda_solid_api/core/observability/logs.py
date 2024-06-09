import contextvars
import logging

import structlog
from colorama import init as colorama_init
from pythonjsonlogger import jsonlogger

from fast_kinda_solid_api.core.settings import ObservabilitySettings

colorama_init(autoreset=True)


logger = structlog.getLogger("fast_kinda_solid_api")


def _add_observability_context(_, __, event_dict):
    """
    Processor to add contextvars from AsyncContextModel to the log.
    """
    for context_var, value in contextvars.copy_context().items():
        if context_var.name.startswith("observability"):
            key = context_var.name.lstrip("observability.")
            event_dict[f"{key}"] = value

    return event_dict


def configure_logging(settings: ObservabilitySettings):
    processors = [
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.processors.TimeStamper(fmt="iso"),
        _add_observability_context,
    ]

    if settings.CONSOLE_LOGGING:
        processors.extend([structlog.dev.set_exc_info, structlog.dev.ConsoleRenderer(colors=True)])
    else:
        processors.append(structlog.processors.JSONRenderer())

    structlog.configure(
        processors=processors,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    handler = logging.StreamHandler()
    if settings.CONSOLE_LOGGING:
        formatter = structlog.stdlib.ProcessorFormatter(
            processor=structlog.dev.ConsoleRenderer(
                colors=True,
                exception_formatter=structlog.dev._format_exception,
            )
        )
        format = "%(message)s"
    else:
        formatter = jsonlogger.JsonFormatter()
        format = "%"

    handler.setFormatter(formatter)
    logging.basicConfig(
        format=format,
        handlers=[handler],
        level=settings.LOG_LEVEL.value,
    )


__all__ = [
    "configure_logging",
]
