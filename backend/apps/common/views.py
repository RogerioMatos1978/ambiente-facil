from rest_framework.response import Response
from rest_framework.views import APIView

from apps.audit.models import AcaoAuditoria, registrar

from .models import ConfiguracaoSistema
from .permissions import IsAdminOrReadOnly
from .serializers import ConfiguracaoSistemaSerializer


class ConfiguracaoSistemaView(APIView):
    """
    GET: qualquer usuário autenticado (usado por todo mundo para saber qual estilo de
    ícone renderizar no menu).
    PUT/PATCH: só administrador (ver IsAdminOrReadOnly) — altera a configuração para
    todo o sistema, registrando o evento na auditoria.
    """

    permission_classes = [IsAdminOrReadOnly]

    def get(self, request):
        config = ConfiguracaoSistema.obter()
        return Response(ConfiguracaoSistemaSerializer(config).data)

    def _atualizar(self, request):
        config = ConfiguracaoSistema.obter()
        anterior = config.estilo_icone
        serializer = ConfiguracaoSistemaSerializer(config, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        if anterior != config.estilo_icone:
            registrar(
                request.user,
                AcaoAuditoria.ATUALIZACAO,
                "ConfiguracaoSistema",
                config.pk,
                descricao=f"Estilo de ícones do sistema alterado de '{anterior}' para '{config.estilo_icone}'.",
                request=request,
            )
        return Response(ConfiguracaoSistemaSerializer(config).data)

    def put(self, request):
        return self._atualizar(request)

    def patch(self, request):
        return self._atualizar(request)
