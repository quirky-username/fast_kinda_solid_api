from abc import ABC, abstractmethod
from contextlib import asynccontextmanager
from enum import Enum, auto
from typing import Type

import structlog
from pydantic_settings import BaseSettings

logger = structlog.getLogger(__name__)


class DependencyState(Enum):
    NOT_STARTED = auto()
    STARTED = auto()
    SHUTDOWN = auto()


class DependencyProvider(ABC):
    """
    Abstract base class for managing dependencies in FastAPI applications.

    This class provides a framework for defining dependencies that require
    setup and teardown logic, such as database connections or external services.
    It ensures that dependencies are properly initialized and cleaned up,
    and it integrates seamlessly with FastAPI's dependency injection system.

    Attributes:
        is_started (bool): Indicates whether the dependency has been started.
        is_shutdown (bool): Indicates whether the dependency has been shut down.

    Methods:
        register(): Class method to register a subclass of DependencyProvider.
        startup(): Method to be implemented by subclasses for
                   initializing resources. This method should contain the logic
                   for setting up the dependency.
        shutdown(): Method to be implemented by subclasses for
                    cleaning up resources. This method should contain the logic
                    for tearing down the dependency.
        provide(): Abstract method to be implemented by subclasses to provide
                   the actual dependency. This method should yield the
                   dependency instance.
        startup_all(cls): Class method to start all registered instances of
                          DependencyProvider subclasses. This is useful for
                          integrating with FastAPI's startup event.
        shutdown_all(cls): Class method to shut down all registered instances of
                           DependencyProvider subclasses. This is useful for
                           integrating with FastAPI's shutdown event.

    Usage:
        Subclasses should implement the `provide` methods to define the
        initialization, cleanup, and provision logic for the dependency.

        ```python
            class AsyncSqlAlchemy(DependencyProvider):
                engine: AsyncEngine
                async_session_maker: async_sessionmaker

                async def startup(self):
                    self.engine = create_async_engine(...)
                    self.async_session_maker = sessionmaker(bind=self.engine)

                async def shutdown(self):
                    await self.engine.dispose()

                async def provide(self):
                    async with self.async_session_maker() as session:
                        yield session
        ```
    """

    _registry: dict[Type["DependencyProvider"], "DependencyProvider"] = {}

    def __new__(cls, *args, **kwargs):
        if cls not in cls._registry:
            instance = super().__new__(cls)
            DependencyProvider._registry[cls] = instance

        return DependencyProvider._registry[cls]

    def __init__(self, settings: BaseSettings):
        self.settings = settings
        self.state = DependencyState.NOT_STARTED

    async def startup(self):
        """Initialize resources."""
        pass

    @abstractmethod
    async def shutdown(self):
        """Cleaning up resources."""
        pass

    @abstractmethod
    @asynccontextmanager
    async def provide(self, **dependencies):
        """Abstract method to provide the actual dependency."""
        pass

    @asynccontextmanager
    async def __call__(self, **dependencies):
        match self.state:
            case DependencyState.NOT_STARTED:
                raise RuntimeError("Dependency has not been started.")
            case DependencyState.STARTED:
                async with self.provide(**dependencies) as dep:
                    yield dep
            case DependencyState.SHUTDOWN:
                raise RuntimeError("Dependency has been shutdown. Cannot provide a shutdown dependency.")

    async def _startup(self):
        match self.state:
            case DependencyState.NOT_STARTED:
                await self.startup()
                self.state = DependencyState.STARTED
            case DependencyState.STARTED:
                logger.warning("Dependency has already been started.")
            case DependencyState.SHUTDOWN:
                raise RuntimeError("Dependency has been shutdown. Cannot start a shutdown dependency.")

    async def _shutdown(self):
        match self.state:
            case DependencyState.NOT_STARTED:
                logger.warning("Dependency has not been started.")
            case DependencyState.STARTED:
                await self.shutdown()
                self.state = DependencyState.SHUTDOWN
            case DependencyState.SHUTDOWN:
                logger.warning("Dependency has already been shutdown.")

    @classmethod
    async def startup_all(cls):
        for dep in DependencyProvider._registry.values():
            await dep.startup()
            dep.state = DependencyState.STARTED

    @classmethod
    async def shutdown_all(cls):
        for dep in DependencyProvider._registry.values():
            await dep.shutdown()
            dep.state = DependencyState.SHUTDOWN


[
    "DependencyProvider",
    "DependencyState",
]
