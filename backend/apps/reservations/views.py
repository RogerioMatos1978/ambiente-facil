from django.utils import timezone
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.audit.models import AcaoAuditoria, registrar
from apps.common.exceptions import exception_handler  # noqa: F401 (garante import cedo)
from apps.common.exports import exportar_csv, exportar_pdf, exportar_xlsx
from apps.common.permissions import IsOwnerOrAdmin
from apps.notifications.services import montar_link_whatsapp

from .filters import ReservaFilter
from .models import Reserva, StatusReserva
from .serializers import CancelarReservaSerializer, ReservaSerializer


class ReservaViewSet(viewsets.ModelViewSet):
    """
    CRUD de reservas com prevenção de conflitos de horário (ver Reserva.clean()).
    Usuários comuns só editam/cancelam suas próprias reservas; administradores gerenciam todas.
    """

    queryset = Reserva.objects.select_related("ambiente", "solicitante").all()
    serializer_class = ReservaSerializer
    permission_classes = [IsAuthenticated, IsOwnerOrAdmin]
    filterset_class = ReservaFilter
    search_fields = ["titulo", "descricao", "ambiente__nome"]
    ordering_fields = ["data_inicio", "data_fim", "criado_em"]
    throttle_scope = "reservations-write"

    def get_queryset(self):
        qs = super().get_queryset()
        if self.request.user.is_admin:
            return qs
        return qs.filter(solicitante=self.request.user)

    def perform_create(self, serializer):
        reserva = serializer.save(solicitante=self.request.user)
        registrar(
            self.request.user,
            AcaoAuditoria.CRIACAO,
            "Reserva",
            reserva.id,
            descricao=f"Reserva '{reserva.titulo}' criada.",
            request=self.request,
        )

    def perform_update(self, serializer):
        reserva = serializer.save()
        registrar(
            self.request.user,
            AcaoAuditoria.ATUALIZACAO,
            "Reserva",
            reserva.id,
            descricao=f"Reserva '{reserva.titulo}' atualizada.",
            request=self.request,
        )

    def perform_destroy(self, instance):
        registrar(
            self.request.user,
            AcaoAuditoria.EXCLUSAO,
            "Reserva",
            instance.id,
            descricao=f"Reserva '{instance.titulo}' excluída.",
            request=self.request,
        )
        instance.delete()

    @action(detail=True, methods=["post"])
    def cancelar(self, request, pk=None):
        """Cancela uma reserva (soft cancel: mantém o registro, muda o status)."""
        reserva = self.get_object()
        serializer = CancelarReservaSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        reserva.status = StatusReserva.CANCELADA
        reserva.motivo_cancelamento = serializer.validated_data.get("motivo", "")
        reserva.cancelado_por = request.user
        reserva.cancelado_em = timezone.now()
        reserva.save()

        registrar(
            request.user,
            AcaoAuditoria.CANCELAMENTO,
            "Reserva",
            reserva.id,
            descricao=f"Reserva '{reserva.titulo}' cancelada.",
            detalhes={"motivo": reserva.motivo_cancelamento},
            request=request,
        )
        return Response(ReservaSerializer(reserva).data)

    @action(detail=True, methods=["get"])
    def whatsapp(self, request, pk=None):
        """Retorna telefone, mensagem e link wa.me prontos para o botão 'Enviar WhatsApp' do frontend."""
        reserva = self.get_object()
        return Response(montar_link_whatsapp(reserva))

    @action(detail=False, methods=["get"], url_path="exportar/(?P<formato>csv|xlsx|pdf)")
    def exportar(self, request, formato=None):
        """Exporta a lista de reservas filtrada (mesmos filtros da listagem) em CSV, Excel ou PDF."""
        queryset = self.filter_queryset(self.get_queryset())
        cabecalhos = ["ID", "Título", "Ambiente", "Solicitante", "Início", "Fim", "Status"]
        linhas = [
            [
                r.id,
                r.titulo,
                r.ambiente.nome,
                r.solicitante.get_full_name(),
                r.data_inicio.strftime("%d/%m/%Y %H:%M"),
                r.data_fim.strftime("%d/%m/%Y %H:%M"),
                r.get_status_display(),
            ]
            for r in queryset
        ]
        registrar(
            request.user,
            AcaoAuditoria.EXPORTACAO,
            "Reserva",
            descricao=f"Exportação de reservas em {formato.upper()}.",
            request=request,
        )
        if formato == "csv":
            return exportar_csv("reservas", cabecalhos, linhas)
        if formato == "xlsx":
            return exportar_xlsx("reservas", cabecalhos, linhas, titulo_planilha="Reservas")
        return exportar_pdf("reservas", "Relatório de Reservas - Ambiente Fácil", cabecalhos, linhas)
