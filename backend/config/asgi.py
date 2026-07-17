"""
Configuração ASGI do projeto Ambiente Fácil.
Expõe o app ASGI com suporte a HTTP e WebSocket (Channels), autenticado via JWT.
"""

import os

from channels.routing import ProtocolTypeRouter, URLRouter
from django.core.asgi import get_asgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.dev")

django_asgi_app = get_asgi_application()

from apps.common.ws_auth import JWTAuthMiddlewareStack  # noqa: E402
from apps.environments.routing import websocket_urlpatterns  # noqa: E402

application = ProtocolTypeRouter(
    {
        "http": django_asgi_app,
        "websocket": JWTAuthMiddlewareStack(URLRouter(websocket_urlpatterns)),
    }
)
