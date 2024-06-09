import asyncio
from concurrent.futures import ThreadPoolExecutor

import pytest
import structlog
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider

from fast_kinda_solid_api.core.observability.tracing import (
    TraceContextModel,
    configure_tracing,
    span_context,
    span_function,
)
from fast_kinda_solid_api.core.settings import OpenTelemetrySettings

logger = structlog.getLogger(__name__)


@pytest.fixture(scope="module")
def setup_tracing():
    settings = OpenTelemetrySettings(ENABLE_CONSOLE_EXPORTER=True, ENABLE_OTEL_EXPORTER=False)
    configure_tracing(settings)

    yield

    tracer_provider = trace.get_tracer_provider()
    if hasattr(tracer_provider, "shutdown"):
        tracer_provider.shutdown()


def test_configure_tracing_with_console_exporter(setup_tracing):
    settings = OpenTelemetrySettings(ENABLE_CONSOLE_EXPORTER=True, ENABLE_OTEL_EXPORTER=False)
    configure_tracing(settings)

    tracer_provider = trace.get_tracer_provider()
    assert isinstance(tracer_provider, TracerProvider)


def test_configure_tracing_with_otlp_exporter(setup_tracing):
    settings = OpenTelemetrySettings(
        ENABLE_CONSOLE_EXPORTER=False,
        ENABLE_OTEL_EXPORTER=True,
        OTLP_ENDPOINT="http://localhost:4317",
        OTLP_PROTOCOL="grpc",
    )
    configure_tracing(settings)

    tracer_provider = trace.get_tracer_provider()
    assert isinstance(tracer_provider, TracerProvider)


@pytest.mark.asyncio
async def test_trace_context_model(setup_tracing):
    async with TraceContextModel.bind(trace_id="12345", span_id="67890"):
        assert TraceContextModel.trace_id.get() == "12345"
        assert TraceContextModel.span_id.get() == "67890"

    with pytest.raises(LookupError):
        TraceContextModel.trace_id.get()

    with pytest.raises(LookupError):
        TraceContextModel.span_id.get()


@pytest.mark.asyncio
async def test_trace_function_decorator(setup_tracing):
    @span_function("test_span")
    async def sample_function():
        return TraceContextModel.trace_id.get(), TraceContextModel.span_id.get()

    tracer = trace.get_tracer(__name__)
    with tracer.start_as_current_span("parent_span"):
        trace_id, span_id = await sample_function()
        assert trace_id is not None
        assert span_id is not None


def test_configure_tracing_with_bad_otlp_protocol(setup_tracing):
    settings = OpenTelemetrySettings(ENABLE_CONSOLE_EXPORTER=False, ENABLE_OTEL_EXPORTER=True, OTLP_PROTOCOL="asdf")
    with pytest.raises(ValueError):
        configure_tracing(settings)


@pytest.mark.asyncio
async def test_span_context():
    tracer = trace.get_tracer(__name__)

    async with span_context(tracer, "test_span_context") as span:
        assert TraceContextModel.trace_id.get() == format(span._context.trace_id, "032x")
        assert TraceContextModel.span_id.get() == format(span._context.span_id, "016x")

    with pytest.raises(LookupError):
        TraceContextModel.trace_id.get()

    with pytest.raises(LookupError):
        TraceContextModel.span_id.get()


@pytest.mark.asyncio
async def test_nested_span_context():
    tracer = trace.get_tracer(__name__)

    async with span_context(tracer, "outer_span") as outer_span:
        async with span_context(tracer, "inner_span") as inner_span:
            assert TraceContextModel.trace_id.get() == format(inner_span._context.trace_id, "032x")
            assert TraceContextModel.span_id.get() == format(inner_span._context.span_id, "016x")

        assert TraceContextModel.trace_id.get() == format(outer_span._context.trace_id, "032x")
        assert TraceContextModel.span_id.get() == format(outer_span._context.span_id, "016x")

    with pytest.raises(LookupError):
        TraceContextModel.trace_id.get()

    with pytest.raises(LookupError):
        TraceContextModel.span_id.get()


@pytest.mark.asyncio
async def test_multithreaded_span_context():
    tracer = trace.get_tracer(__name__)

    async def span_task(span_name):
        async with span_context(tracer, span_name):
            return TraceContextModel.trace_id.get(), TraceContextModel.span_id.get()

    def run_task_in_thread(loop, span_name):
        asyncio.set_event_loop(loop)
        return loop.run_until_complete(span_task(span_name))

    loop1 = asyncio.new_event_loop()
    loop2 = asyncio.new_event_loop()

    with ThreadPoolExecutor() as executor:
        future1 = executor.submit(run_task_in_thread, loop1, "thread_span_1")
        future2 = executor.submit(run_task_in_thread, loop2, "thread_span_2")

        trace_id1, span_id1 = future1.result()
        trace_id2, span_id2 = future2.result()

        assert trace_id1 is not None
        assert span_id1 is not None
        assert trace_id2 is not None
        assert span_id2 is not None
        assert trace_id1 != trace_id2
        assert span_id1 != span_id2

    loop1.close()
    loop2.close()
