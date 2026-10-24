from __future__ import annotations

from rest_framework.views import exception_handler


def api_exception_handler(exc, context):
    response = exception_handler(exc, context)
    if response is None:
        return None
    data = response.data
    if isinstance(data, dict) and "code" in data and "message" in data:
        return response
    message = "Erro de validação"
    if isinstance(data, dict):
        if "detail" in data:
            message = str(data["detail"])
        else:
            message = str(data)
    elif isinstance(data, list):
        message = "; ".join(str(x) for x in data)
    response.data = {
        "code": "error",
        "message": message,
        "details": data if isinstance(data, (dict, list)) else {},
    }
    return response
