import uuid

from fastapi import Request

from fast_kinda_solid_api.contexts import RequestContext


async def add_correlation_ids(request: Request, call_next):
    request_id = str(uuid.uuid4())
    RequestContext.request_id.set(request_id)
    request.state.request_id = request_id

    response = await call_next(request)

    response.headers["X-API-Request-ID"] = request_id

    # connection_id = context.connection_id
    # if connection_id:
    #     response.headers['X-API-Connection-ID'] = connection_id

    # session_id = context.session_id
    # if session_id:
    #     response.headers['X-API-Session-ID'] = RequestContext.current().session_id

    # transaction_id = context.transaction_id
    # if transaction_id:
    #     response.headers['X-API-Transaction-ID'] = transaction_id

    return response


__all__ = [
    "add_correlation_ids",
]
