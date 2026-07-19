from django.core.exceptions import ValidationError as DjangoValidationError
from django.utils import timezone
from rest_framework import serializers

from apps.environments.models import Ambiente
from apps.environments.serializers import AmbienteSerializer

from .models import Reserva, StatusReserva


class ReservaSerializer(serializers.ModelSerializer):
    ambiente_detalhe = AmbienteSerializer(source="ambiente", read_only=True)
    solicitante_nome = serializers.CharField(source="solicitante.get_full_name", read_only=True)
    precisa_checkin = serializers.BooleanField(read_only=True)
    prazo_checkin = serializers.DateTimeField(read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)

    class Meta:
        model = Reserva
        fields = [
            "id",
            "ambiente",
            "ambiente_detalhe",
            "solicitante",
            "solicitante_nome",
            "titulo",
            "descricao",
            "data_inicio",
            "data_fim",
            "status",
            "status_display",
            "motivo_cancelamento",
            "cancelado_por",
            "cancelado_em",
            "notificar_email",
            "checkin_confirmado_em",
            "precisa_checkin",
            "prazo_checkin",
            "criado_em",
            "atualizado_em",
        ]
        read_only_fields = [
            "solicitante",
            "cancelado_por",
            "cancelado_em",
            "checkin_confirmado_em",
            "criado_em",
            "atualizado_em",
        ]

    def validate(self, attrs):
        # Reservas já concluídas, canceladas ou expiradas (ou cujo período já passou) são
        # somente leitura: nenhum campo pode mais ser alterado, nem por administrador.
        if self.instance is not None:
            editavel = (
                self.instance.status in (StatusReserva.PENDENTE, StatusReserva.CONFIRMADA)
                and self.instance.data_fim > timezone.now()
            )
            if not editavel:
                raise serializers.ValidationError(
                    {"detalhes": "Esta reserva já foi concluída, cancelada ou expirada e não pode mais ser alterada."}
                )

        instancia = Reserva(
            id=self.instance.id if self.instance else None,
            ambiente=attrs.get("ambiente", getattr(self.instance, "ambiente", None)),
            data_inicio=attrs.get("data_inicio", getattr(self.instance, "data_inicio", None)),
            data_fim=attrs.get("data_fim", getattr(self.instance, "data_fim", None)),
            status=attrs.get("status", getattr(self.instance, "status", StatusReserva.CONFIRMADA)),
        )
        try:
            instancia.clean()
        except DjangoValidationError as exc:
            raise serializers.ValidationError({"conflito": exc.messages})
        return attrs


class CancelarReservaSerializer(serializers.Serializer):
    motivo = serializers.CharField(max_length=255, required=False, allow_blank=True)


DURACOES_PERMITIDAS = (15, 30, 45, 60, 90, 120)


class ReservaRapidaSerializer(serializers.Serializer):
    """Fluxo de 1 clique: reserva o ambiente escolhido a partir de agora, por uma duração curta."""

    ambiente = serializers.PrimaryKeyRelatedField(queryset=Ambiente.objects.filter(ativo=True))
    duracao_minutos = serializers.ChoiceField(choices=DURACOES_PERMITIDAS, default=30)
    titulo = serializers.CharField(max_length=200, required=False, allow_blank=True)
