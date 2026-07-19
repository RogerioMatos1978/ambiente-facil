"""Middleware simples de auditoria/observabilidade de requisições."""

import logging
import time

logger = logging.getLogger("apps.common")


class RequestLoggingMiddleware:
    """Registra método, caminho, usuário, status e tempo de resposta de cada requisição."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        start = time.monotonic()
        response = self.get_response(request)
        duration_ms = (time.monotonic() - start) * 1000
        user = getattr(request, "user", None)
        username = getattr(user, "username", "anônimo") if user and user.is_authenticated else "anônimo"
        logger.info(
            "%s %s status=%s usuario=%s tempo=%.1fms",
            request.method,
            request.path,
            response.status_code,
            username,
            duration_ms,
        )
        return response
