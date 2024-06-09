from contextvars import ContextVar

from fast_kinda_solid_api.observability.context import BaseContext


class RequestContext(BaseContext):
    connection_id: ContextVar[str] = ContextVar("observability.request.connection_id")
    session_id: ContextVar[str] = ContextVar("observability.request.session_id")
    request_id: ContextVar[str] = ContextVar("observability.request.request_id")
    transaction_id: ContextVar[str] = ContextVar("observability.request.transaction_id")


class RepositoryOperationContext(BaseContext):
    transaction_id: ContextVar[str] = ContextVar("observability.request.transaction_id")
    model_class: ContextVar[str] = ContextVar("observability.request.model_class")
    input_dto_class: ContextVar[str] = ContextVar("observability.request.input_dto_class")
    output_dto_class: ContextVar[str] = ContextVar("observability.request.output_dto_class")
