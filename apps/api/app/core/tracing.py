import uuid
from contextvars import ContextVar

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint

TRACE_ID_HEADER = "X-Request-ID"
trace_id_context: ContextVar[str | None] = ContextVar("trace_id", default=None)


def get_trace_id() -> str:
    trace_id = trace_id_context.get()
    if trace_id is None:
        trace_id = uuid.uuid4().hex
        trace_id_context.set(trace_id)
    return trace_id


class RequestTracingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        settings = getattr(request.app.state, "settings", None)
        enabled = getattr(getattr(settings, "feature_flags", None), "request_tracing_enabled", True)

        incoming_trace_id = request.headers.get(TRACE_ID_HEADER)
        trace_id = incoming_trace_id.strip() if incoming_trace_id else uuid.uuid4().hex
        token = trace_id_context.set(trace_id)

        try:
            response = await call_next(request)
        finally:
            trace_id_context.reset(token)

        if enabled:
            response.headers[TRACE_ID_HEADER] = trace_id
        return response
