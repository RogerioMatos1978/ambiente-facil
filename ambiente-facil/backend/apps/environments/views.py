import io

import qrcode
from django.conf import settings
from django.http import HttpResponse
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny

from apps.common.permissions import IsAdminOrReadOnly, NaoEhVigilante

from .models import Ambiente
from .serializers import AmbienteSerializer


class AmbienteViewSet(viewsets.ModelViewSet):
    """CRUD de ambientes. Leitura liberada a todo usuário autenticado; escrita apenas para admins."""

    queryset = Ambiente.objects.all()
    serializer_class = AmbienteSerializer
    permission_classes = [IsAdminOrReadOnly, NaoEhVigilante]
    filterset_fields = ["tipo", "ativo", "localizacao"]
    search_fields = ["nome", "localizacao", "descricao"]
    ordering_fields = ["nome", "capacidade", "criado_em"]

    @action(detail=True, methods=["get"], permission_classes=[AllowAny])
    def qrcode(self, request, pk=None):
        """
        Gera um QR code (PNG) apontando para a página de check-in/reserva
        rápida deste ambiente no frontend (`/checkin/<id>`). Pensado para
        ser impresso e colado na porta da sala.
        """
        ambiente = self.get_object()
        frontend_url = settings.FRONTEND_URL.rstrip("/")
        destino = f"{frontend_url}/checkin/{ambiente.id}"

        imagem = qrcode.make(destino, box_size=8, border=2)
        buffer = io.BytesIO()
        imagem.save(buffer, format="PNG")
        resposta = HttpResponse(buffer.getvalue(), content_type="image/png")
        resposta["Cache-Control"] = "no-cache"
        return resposta
