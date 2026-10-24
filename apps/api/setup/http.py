from __future__ import annotations


def client_ip(request) -> str | None:
    fwd = request.META.get("HTTP_X_FORWARDED_FOR")
    if fwd:
        return fwd.split(",")[0].strip() or None
    return request.META.get("REMOTE_ADDR") or None
