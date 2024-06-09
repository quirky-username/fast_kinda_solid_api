from contextlib import asynccontextmanager
from contextvars import ContextVar
from functools import wraps
from typing import Any, Awaitable, Callable, TypeVar

from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.exporter.otlp.proto.http.trace_exporter import (
    OTLPSpanExporter as OTLPHTTPSpanExporter,
)
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter
from opentelemetry.trace import NonRecordingSpan, SpanKind
from structlog import getLogger

from fast_kinda_solid_api.core.observability.context import BaseObservabilityContext
from fast_kinda_solid_api.core.settings import OpenTelemetrySettings

logger = getLogger(__name__)


F = TypeVar("F", bound=Callable[..., Awaitable[Any]])


def configure_tracing(settings: OpenTelemetrySettings):
    provider = TracerProvider()
    trace.set_tracer_provider(provider)

    if settings.ENABLE_CONSOLE_EXPORTER:
        console_exporter = ConsoleSpanExporter()
        provider.add_span_processor(BatchSpanProcessor(console_exporter))
        logger.info("ConsoleSpanExporter enabled")

    if settings.ENABLE_OTEL_EXPORTER:
        exporter_params = {
            "endpoint": settings.OTLP_ENDPOINT,
            "insecure": settings.INSECURE,
            "headers": settings.HEADERS or {},
            "timeout": settings.TIMEOUT,
        }

        if settings.AUTH_TOKEN:
            exporter_params["headers"]["Authorization"] = f"Bearer {settings.AUTH_TOKEN}"  # type: ignore

        if settings.OTLP_PROTOCOL == "grpc":
            otlp_exporter = OTLPSpanExporter(**exporter_params)
        elif settings.OTLP_PROTOCOL == "http/protobuf":
            otlp_exporter = OTLPHTTPSpanExporter(**exporter_params)
        else:
            raise ValueError("Unsupported OTLP protocol")

        span_processor = BatchSpanProcessor(otlp_exporter)
        provider.add_span_processor(span_processor)
        logger.info("OTLP exporter configured successfully")

    logger.info("OpenTelemetry tracing configured.")


class TraceContextModel(BaseObservabilityContext):
    trace_id: ContextVar[str] = ContextVar("observability.trace_id")
    span_id: ContextVar[str] = ContextVar("observability.span_id")


def span_function(span_name: str):
    def decorator(func: F) -> F:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            tracer = trace.get_tracer(__name__)
            with tracer.start_as_current_span(span_name, kind=SpanKind.INTERNAL) as span:
                if isinstance(span, NonRecordingSpan):
                    return await func(*args, **kwargs)
                else:
                    trace_id = format(span.context.trace_id, "032x")
                    span_id = format(span.context.span_id, "016x")
                    async with TraceContextModel.bind(trace_id=trace_id, span_id=span_id):
                        result = await func(*args, **kwargs)
                    return result

        return wrapper  # type: ignore

    return decorator


@asynccontextmanager
async def span_context(tracer, span_name, **span_kwargs):
    with tracer.start_as_current_span(span_name, kind=SpanKind.INTERNAL, **span_kwargs) as span:
        trace_id = format(span._context.trace_id, "032x")
        span_id = format(span._context.span_id, "016x")
        async with TraceContextModel.bind(trace_id=trace_id, span_id=span_id):
            yield span


__all__ = [
    "TraceContextModel",
    "configure_tracing",
    "span_function",
]
