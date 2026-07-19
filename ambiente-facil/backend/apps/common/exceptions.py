"""Handler global de exceções para respostas de erro padronizadas."""

import logging

from rest_framework.views import exception_handler as drf_exception_handler

logger = logging.getLogger("apps.common")


def exception_handler(exc, context):
    response = drf_exception_handler(exc, context)
    if response is not None:
        request = context.get("request")
        logger.warning(
            "Erro tratado: %s | path=%s | detail=%s",
            exc.__class__.__name__,
            getattr(request, "path", "-"),
            response.data,
        )
        response.data = {
            "erro": True,
            "codigo": response.status_code,
            "detalhes": response.data,
        }
    return response
