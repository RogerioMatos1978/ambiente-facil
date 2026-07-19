"""Middleware de autenticação JWT para conexões WebSocket (Django Channels).

O cliente (frontend) se conecta em algo como:
  wss://.../ws/painel-ambientes/?token=<access_token>
Este middleware decodifica o token JWT (mesmo usado na API REST) e popula
scope["user"] com o usuário autenticado, ou AnonymousUser caso inválido/ausente.
"""

from urllib.parse import parse_qs

from channels.db import database_sync_to_async
from channels.middleware import BaseMiddleware
from django.contrib.auth.models import AnonymousUser
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from rest_framework_simplejwt.tokens import AccessToken


@database_sync_to_async
def obter_usuario_do_token(token: str):
    from django.contrib.auth import get_user_model

    User = get_user_model()
    try:
        validado = AccessToken(token)
        return User.objects.get(id=validado["user_id"])
    except (InvalidToken, TokenError, User.DoesNotExist, KeyError):
        return AnonymousUser()


class JWTAuthMiddleware(BaseMiddleware):
    async def __call__(self, scope, receive, send):
        query_string = parse_qs(scope.get("query_string", b"").decode())
        token = query_string.get("token", [None])[0]
        scope["user"] = await obter_usuario_do_token(token) if token else AnonymousUser()
        return await super().__call__(scope, receive, send)


def JWTAuthMiddlewareStack(inner):
    return JWTAuthMiddleware(inner)
