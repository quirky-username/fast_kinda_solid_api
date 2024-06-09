from typing import Set

import uvicorn
from fastapi import FastAPI
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

from fast_kinda_solid_api.config import ServerSettings
from fast_kinda_solid_api.observability.logs import configure_logging, logger
from fast_kinda_solid_api.observability.tracing import configure_tracing


class InitializationError(Exception):
    """Custom exception for initialization errors."""


class BaseAPIServer(FastAPI):
    """A custom FastAPI server class with additional functionalities for observability and error handling."""

    _registered_server_names: Set[str] = set()

    def __init__(self, name: str, *args, settings=ServerSettings, **kwargs):
        """
        Initialize the BaseAPIServer instance.

        Args:
            name (str): The name of the server.
            include_exception_handlers (bool): Whether to include custom exception handlers. Defaults to True.
            settings: Server settings, defaults to ServerSettings.
            *args: Additional arguments for FastAPI initialization.
            **kwargs: Additional keyword arguments for FastAPI initialization.
        """
        self.settings = settings
        configure_logging(self.settings.OBSERVABILITY_SETTINGS)
        configure_tracing(self.settings.OTEL_SETTINGS)
        self._register_name(name)

        super().__init__(*args, **kwargs)
        logger.info("Initialized FastAPI app")

        FastAPIInstrumentor.instrument_app(self)
        logger.info("Instrumented FastAPI app for OpenTelemetry tracing")

    def run(self):
        """
        Run the FastAPI server using Uvicorn.

        This method starts the server with the specified host, port, and reload settings
        from the server settings.
        """

        # self.middleware("http")(add_correlation_ids)
        logger.debug("Starting uvicorn server")
        uvicorn.run(
            self,
            host=self.settings.HOST,
            port=self.settings.PORT,
            reload=self.settings.RELOAD,
        )

    def _register_name(self, name: str) -> None:
        """
        Register the server name to ensure uniqueness.

        Args:
            name (str): The name of the server.

        Raises:
            ValueError: If the server name is already registered.
        """
        if name in BaseAPIServer._registered_server_names:
            raise ValueError(f"BaseAPIServer {name} is already registered.")

        BaseAPIServer._registered_server_names.add(name)
        self.name = name


__all__ = [
    "BaseAPIServer",
    "InitializationError",
]
