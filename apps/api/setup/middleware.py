from __future__ import annotations

import logging
import uuid

from django.utils.deprecation import MiddlewareMixin

correlation_local = __import__("contextvars").ContextVar("correlation_id", default="-")


class CorrelationIdMiddleware(MiddlewareMixin):
    def process_request(self, request):
        cid = request.headers.get("X-Correlation-Id") or str(uuid.uuid4())
        correlation_local.set(cid)
        request.correlation_id = cid

    def process_response(self, request, response):
        cid = getattr(request, "correlation_id", None) or correlation_local.get()
        response["X-Correlation-Id"] = cid
        return response


class CorrelationIdFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        record.correlation_id = correlation_local.get("-")
        return True
