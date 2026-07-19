from django.core.exceptions import ValidationError as DjangoValidationError
from django.db.models import Avg, Count, DurationField, ExpressionWrapper, F
from django.db.models.functions import TruncDate
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
from .serializers import CancelarReservaSerializer, ReservaRapidaSerializer, ReservaSerializer


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

    @action(detail=True, methods=["post"])
    def checkin(self, request, pk=None):
        """
        Confirma presença na reserva (check-in). Só se aplica a ambientes com
        `exige_checkin=True`. Enquanto não confirmado, a reserva pode ser
        liberada automaticamente por no-show (ver management command
        `liberar_no_show`).
        """
        reserva = self.get_object()
        if reserva.status != StatusReserva.CONFIRMADA:
            return Response(
                {"detail": "Só é possível fazer check-in em reservas confirmadas."}, status=400
            )
        if reserva.checkin_confirmado_em is not None:
            return Response({"detail": "Check-in já confirmado para esta reserva."}, status=400)

        reserva.checkin_confirmado_em = timezone.now()
        reserva.save()

        registrar(
            request.user,
            AcaoAuditoria.ATUALIZACAO,
            "Reserva",
            reserva.id,
            descricao=f"Check-in confirmado para '{reserva.titulo}'.",
            request=request,
        )
        return Response(ReservaSerializer(reserva).data)

    @action(detail=False, methods=["post"])
    def rapida(self, request):
        """
        Reserva rápida: cria uma reserva começando agora, por uma duração
        curta pré-definida (15/30/45/60/90/120 min) — fluxo de 1 clique
        usado no botão "Reservar agora" do dashboard e na página de QR code.
        """
        serializer = ReservaRapidaSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        agora = timezone.now()
        ambiente = serializer.validated_data["ambiente"]
        duracao = int(serializer.validated_data["duracao_minutos"])
        titulo = serializer.validated_data.get("titulo") or (
            f"Reserva rápida - {request.user.get_full_name() or request.user.username}"
        )

        reserva = Reserva(
            ambiente=ambiente,
            solicitante=request.user,
            titulo=titulo,
            data_inicio=agora,
            data_fim=agora + timezone.timedelta(minutes=duracao),
            status=StatusReserva.CONFIRMADA,
            notificar_email=False,
        )
        try:
            reserva.save()
        except DjangoValidationError as exc:
            return Response({"detalhes": {"conflito": exc.messages}}, status=400)

        registrar(
            request.user,
            AcaoAuditoria.CRIACAO,
            "Reserva",
            reserva.id,
            descricao=f"Reserva rápida '{reserva.titulo}' criada.",
            request=request,
        )
        return Response(ReservaSerializer(reserva).data, status=201)

    @action(detail=True, methods=["get"])
    def whatsapp(self, request, pk=None):
        """Retorna telefone, mensagem e link wa.me prontos para o botão 'Enviar WhatsApp' do frontend."""
        reserva = self.get_object()
        return Response(montar_link_whatsapp(reserva))

    @action(detail=False, methods=["get"])
    def relatorio(self, request):
        """
        Relatório agregado de reservas: KPIs (total, por status, taxa de no-show,
        duração média), série de reservas por dia e rankings por ambiente e por
        solicitante (este último só para administradores). Aceita os mesmos
        filtros da listagem (ambiente, solicitante, status, data_de, data_ate).
        """
        queryset = self.filter_queryset(self.get_queryset())

        total = queryset.count()
        status_labels = dict(StatusReserva.choices)
        por_status = [
            {
                "status": item["status"],
                "status_display": status_labels.get(item["status"], item["status"]),
                "total": item["total"],
            }
            for item in queryset.values("status").annotate(total=Count("id")).order_by("-total")
        ]

        confirmadas = queryset.filter(status=StatusReserva.CONFIRMADA).count()
        canceladas = queryset.filter(status=StatusReserva.CANCELADA).count()
        concluidas = queryset.filter(status=StatusReserva.CONCLUIDA).count()
        pendentes = queryset.filter(status=StatusReserva.PENDENTE).count()
        expiradas = queryset.filter(status=StatusReserva.EXPIRADA).count()

        base_no_show = confirmadas + concluidas + expiradas
        taxa_no_show = round((expiradas / base_no_show) * 100, 1) if base_no_show else 0.0

        duracao_media = queryset.annotate(
            duracao=ExpressionWrapper(F("data_fim") - F("data_inicio"), output_field=DurationField())
        ).aggregate(media=Avg("duracao"))["media"]
        duracao_media_minutos = round(duracao_media.total_seconds() / 60) if duracao_media else 0

        por_dia = [
            {"dia": item["dia"].isoformat(), "total": item["total"]}
            for item in queryset.annotate(dia=TruncDate("data_inicio"))
            .values("dia")
            .annotate(total=Count("id"))
            .order_by("dia")
        ]

        por_ambiente = [
            {"ambiente_id": item["ambiente_id"], "ambiente_nome": item["ambiente__nome"], "total": item["total"]}
            for item in queryset.values("ambiente_id", "ambiente__nome").annotate(total=Count("id")).order_by("-total")[:10]
        ]

        por_solicitante = []
        if request.user.is_admin:
            solicitantes_qs = (
                queryset.values(
                    "solicitante_id", "solicitante__first_name", "solicitante__last_name", "solicitante__username"
                )
                .annotate(total=Count("id"))
                .order_by("-total")[:10]
            )
            for item in solicitantes_qs:
                nome = (
                    f"{item['solicitante__first_name']} {item['solicitante__last_name']}".strip()
                    or item["solicitante__username"]
                )
                por_solicitante.append(
                    {"solicitante_id": item["solicitante_id"], "solicitante_nome": nome, "total": item["total"]}
                )

        return Response(
            {
                "resumo": {
                    "total": total,
                    "confirmadas": confirmadas,
                    "canceladas": canceladas,
                    "concluidas": concluidas,
                    "pendentes": pendentes,
                    "expiradas": expiradas,
                    "taxa_no_show": taxa_no_show,
                    "duracao_media_minutos": duracao_media_minutos,
                },
                "por_status": por_status,
                "por_dia": por_dia,
                "por_ambiente": por_ambiente,
                "por_solicitante": por_solicitante,
            }
        )

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
