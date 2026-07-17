from rest_framework import viewsets

from apps.common.permissions import IsAdmin

from .models import LogAuditoria
from .serializers import LogAuditoriaSerializer


class LogAuditoriaViewSet(viewsets.ReadOnlyModelViewSet):
    """Consulta de logs de auditoria. Apenas administradores têm acesso."""

    queryset = LogAuditoria.objects.select_related("usuario").all()
    serializer_class = LogAuditoriaSerializer
    permission_classes = [IsAdmin]
    filterset_fields = ["acao", "entidade", "usuario"]
    search_fields = ["descricao", "entidade"]
