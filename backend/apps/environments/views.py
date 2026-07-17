from rest_framework import viewsets

from apps.common.permissions import IsAdminOrReadOnly

from .models import Ambiente
from .serializers import AmbienteSerializer


class AmbienteViewSet(viewsets.ModelViewSet):
    """CRUD de ambientes. Leitura liberada a todo usuário autenticado; escrita apenas para admins."""

    queryset = Ambiente.objects.all()
    serializer_class = AmbienteSerializer
    permission_classes = [IsAdminOrReadOnly]
    filterset_fields = ["tipo", "ativo", "localizacao"]
    search_fields = ["nome", "localizacao", "descricao"]
    ordering_fields = ["nome", "capacidade", "criado_em"]
