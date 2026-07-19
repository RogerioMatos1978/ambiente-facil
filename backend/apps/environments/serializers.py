from rest_framework import serializers

from .models import Ambiente


class AmbienteSerializer(serializers.ModelSerializer):
    status_atual = serializers.SerializerMethodField()
    reserva_atual = serializers.SerializerMethodField()

    class Meta:
        model = Ambiente
        fields = [
            "id",
            "nome",
            "tipo",
            "localizacao",
            "capacidade",
            "recursos",
            "descricao",
            "foto",
            "ativo",
            "exige_checkin",
            "tolerancia_checkin_minutos",
            "status_atual",
            "reserva_atual",
            "criado_em",
            "atualizado_em",
        ]

    def _reserva_em_uso_agora(self, obj):
        from django.utils import timezone

        agora = timezone.now()
        return (
            obj.reservas.filter(status="confirmada", data_inicio__lte=agora, data_fim__gte=agora)
            .select_related("solicitante")
            .order_by("data_fim")
            .first()
        )

    def get_status_atual(self, obj) -> str:
        return "ocupado" if self._reserva_em_uso_agora(obj) else "livre"

    def get_reserva_atual(self, obj):
        """
        Resumo da reserva que está ocupando o ambiente agora — usado no Painel em
        tempo real para mostrar quando a reserva termina e, ao passar o mouse, os
        detalhes completos. `None` quando o ambiente está livre.
        """
        reserva = self._reserva_em_uso_agora(obj)
        if not reserva:
            return None
        return {
            "id": reserva.id,
            "numero_controle": reserva.numero_controle,
            "titulo": reserva.titulo,
            "solicitante_nome": reserva.solicitante.get_full_name() or reserva.solicitante.username,
            "reservado_para_categoria_display": reserva.get_reservado_para_categoria_display(),
            "reservado_para_nome": reserva.reservado_para_nome,
            "reservado_para_telefone": reserva.reservado_para_telefone,
            "data_inicio": reserva.data_inicio,
            "data_fim": reserva.data_fim,
            "duracao_display": reserva.duracao_display,
        }
