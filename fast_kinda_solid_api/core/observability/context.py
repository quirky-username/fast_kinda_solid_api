from contextvars import ContextVar

from fastapi.concurrency import asynccontextmanager
from pydantic_settings import BaseSettings


class ContextSettings(BaseSettings):
    CONTEXT_VAR_PREFIX: str = "observability."


class BaseObservabilityContext:
    @classmethod
    @asynccontextmanager
    async def bind(cls, **kwargs):
        tokens = dict()
        for key, value in kwargs.items():
            attribute_definition = getattr(cls, key, None)
            if isinstance(attribute_definition, ContextVar):
                setter = getattr(attribute_definition, "set")
                token = setter(value)
                tokens[key] = token

        yield
        for key, token in tokens.items():
            getattr(cls, key).reset(token)


class RepositoryOperationContext(BaseObservabilityContext):
    transaction_id: ContextVar[str] = ContextVar("observability.request.transaction_id")
    model_class: ContextVar[str] = ContextVar("observability.request.model_class")
    input_dto_class: ContextVar[str] = ContextVar("observability.request.input_dto_class")
    output_dto_class: ContextVar[str] = ContextVar("observability.request.output_dto_class")


class RequestContext(BaseObservabilityContext):
    session_id: str
    transaction_id: str
    connection_id: str


__all__ = [
    "ContextSettings",
    "BaseObservabilityContext",
    "RepositoryOperationContext",
    "RequestContext",
]
