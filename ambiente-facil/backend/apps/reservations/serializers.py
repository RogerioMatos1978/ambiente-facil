from django.core.exceptions import ValidationError as DjangoValidationError
from django.utils import timezone
from rest_framework import serializers

from apps.environments.models import Ambiente
from apps.environments.serializers import AmbienteSerializer

from .models import CategoriaReservadoPara, Reserva, StatusReserva


class ReservaSerializer(serializers.ModelSerializer):
    ambiente_detalhe = AmbienteSerializer(source="ambiente", read_only=True)
    solicitante_nome = serializers.CharField(source="solicitante.get_full_name", read_only=True)
    numero_controle = serializers.CharField(read_only=True)
    duracao_horas = serializers.FloatField(read_only=True)
    duracao_display = serializers.CharField(read_only=True)
    precisa_checkin = serializers.BooleanField(read_only=True)
    prazo_checkin = serializers.DateTimeField(read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    mensagem_guarita = serializers.CharField(read_only=True)
    reservado_para_categoria_display = serializers.CharField(
        source="get_reservado_para_categoria_display", read_only=True
    )
    chave_status = serializers.SerializerMethodField()
    chave_status_display = serializers.SerializerMethodField()
    chave_atrasada = serializers.SerializerMethodField()
    # Obrigatórios no formulário padrão de nova reserva (reserva rápida via QR code
    # preenche com valores padrão automaticamente — ver ReservaViewSet.rapida).
    reservado_para_categoria = serializers.ChoiceField(choices=CategoriaReservadoPara.choices, required=True)
    reservado_para_nome = serializers.CharField(max_length=150, required=True, allow_blank=False)
    reservado_para_telefone = serializers.CharField(max_length=20, required=True, allow_blank=False)

    class Meta:
        model = Reserva
        fields = [
            "id",
            "numero_controle",
            "duracao_horas",
            "duracao_display",
            "ambiente",
            "ambiente_detalhe",
            "solicitante",
            "solicitante_nome",
            "titulo",
            "descricao",
            "reservado_para_categoria",
            "reservado_para_categoria_display",
            "reservado_para_nome",
            "reservado_para_telefone",
            "mensagem_guarita",
            "chave_status",
            "chave_status_display",
            "chave_atrasada",
            "data_inicio",
            "data_fim",
            "status",
            "status_display",
            "motivo_cancelamento",
            "cancelado_por",
            "cancelado_em",
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

    def get_chave_status(self, obj):
        # Não precisa importar apps.keys aqui: "chave" é o related_name reverso do
        # OneToOneField em Chave.ambiente (ver apps/keys/models.py), então dá pra
        # acessar via getattr sem criar nenhuma dependência de import entre os apps.
        chave = getattr(obj.ambiente, "chave", None)
        return chave.status if chave else None

    def get_chave_status_display(self, obj):
        chave = getattr(obj.ambiente, "chave", None)
        return chave.get_status_display() if chave else "Não cadastrada"

    def get_chave_atrasada(self, obj):
        """
        True quando a chave desta reserva está ocupada (retirada, ainda não devolvida
        na guarita) e já passou da tolerância de devolução após o fim do período —
        usado pelo frontend para pintar a linha de amarelo na lista de Reservas.
        """
        from django.conf import settings

        chave = getattr(obj.ambiente, "chave", None)
        if not chave or chave.status != "ocupada" or chave.reserva_atual_id != obj.id:
            return False
        tolerancia = getattr(settings, "CHAVE_TOLERANCIA_DEVOLUCAO_MINUTOS", 10)
        return timezone.now() > obj.data_fim + timezone.timedelta(minutes=tolerancia)


class CancelarReservaSerializer(serializers.Serializer):
    motivo = serializers.CharField(max_length=255, required=False, allow_blank=True)


DURACOES_PERMITIDAS = (15, 30, 45, 60, 90, 120)


class ReservaRapidaSerializer(serializers.Serializer):
    """Fluxo de 1 clique: reserva o ambiente escolhido a partir de agora, por uma duração curta."""

    ambiente = serializers.PrimaryKeyRelatedField(queryset=Ambiente.objects.filter(ativo=True))
    duracao_minutos = serializers.ChoiceField(choices=DURACOES_PERMITIDAS, default=30)
    titulo = serializers.CharField(max_length=200, required=False, allow_blank=True)
