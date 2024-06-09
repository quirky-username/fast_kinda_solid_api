from contextvars import ContextVar

from fastapi.concurrency import asynccontextmanager


class BaseContext:
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
