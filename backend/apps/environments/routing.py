from django.urls import re_path

from .consumers import PainelAmbientesConsumer

websocket_urlpatterns = [
    re_path(r"^ws/painel-ambientes/$", PainelAmbientesConsumer.as_asgi()),
]
