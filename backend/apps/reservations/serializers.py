from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers

from apps.environments.serializers import AmbienteSerializer

from .models import Reserva, StatusReserva


class ReservaSerializer(serializers.ModelSerializer):
    ambiente_detalhe = AmbienteSerializer(source="ambiente", read_only=True)
    solicitante_nome = serializers.CharField(source="solicitante.get_full_name", read_only=True)

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
            "motivo_cancelamento",
            "cancelado_por",
            "cancelado_em",
            "notificar_email",
            "criado_em",
            "atualizado_em",
        ]
        read_only_fields = ["solicitante", "cancelado_por", "cancelado_em", "criado_em", "atualizado_em"]

    def validate(self, attrs):
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
