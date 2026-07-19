from django.utils import timezone
from rest_framework import serializers

from apps.reservations.models import Reserva, StatusReserva

from .models import Chave


class ReservaResumoGuaritaSerializer(serializers.ModelSerializer):
    """Recorte enxuto de Reserva para a Guarita — não passa pelo ReservaSerializer/
    ReservaViewSet (o vigilante não tem acesso a eles, ver NaoEhVigilante)."""

    solicitante_nome = serializers.CharField(source="solicitante.get_full_name", read_only=True)
    reservado_para_categoria_display = serializers.CharField(
        source="get_reservado_para_categoria_display", read_only=True
    )
    status_display = serializers.CharField(source="get_status_display", read_only=True)

    class Meta:
        model = Reserva
        fields = [
            "id",
            "numero_controle",
            "titulo",
            "solicitante_nome",
            "data_inicio",
            "data_fim",
            "duracao_display",
            "status",
            "status_display",
            "reservado_para_categoria",
            "reservado_para_categoria_display",
            "reservado_para_nome",
            "reservado_para_telefone",
        ]


class ChaveSerializer(serializers.ModelSerializer):
    ambiente_nome = serializers.CharField(source="ambiente.nome", read_only=True)
    ambiente_localizacao = serializers.CharField(source="ambiente.localizacao", read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    retirada_por_nome = serializers.CharField(source="retirada_por.get_full_name", read_only=True)
    reserva_atual_detalhe = ReservaResumoGuaritaSerializer(source="reserva_atual", read_only=True)
    reservas_hoje = serializers.SerializerMethodField()

    class Meta:
        model = Chave
        fields = [
            "id",
            "ambiente",
            "ambiente_nome",
            "ambiente_localizacao",
            "status",
            "status_display",
            "reserva_atual",
            "reserva_atual_detalhe",
            "retirada_em",
            "retirada_por",
            "retirada_por_nome",
            "devolvida_em",
            "reservas_hoje",
            "atualizado_em",
        ]
        read_only_fields = ["ambiente", "reserva_atual", "retirada_em", "retirada_por", "devolvida_em", "atualizado_em"]

    def get_reservas_hoje(self, obj):
        inicio_dia = timezone.localtime().replace(hour=0, minute=0, second=0, microsecond=0)
        fim_dia = inicio_dia + timezone.timedelta(days=1)
        reservas = Reserva.objects.filter(
            ambiente=obj.ambiente,
            status__in=[StatusReserva.PENDENTE, StatusReserva.CONFIRMADA],
            data_inicio__lt=fim_dia,
            data_fim__gt=inicio_dia,
        ).select_related("solicitante").order_by("data_inicio")
        return ReservaResumoGuaritaSerializer(reservas, many=True).data
