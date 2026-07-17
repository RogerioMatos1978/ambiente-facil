from rest_framework import serializers

from .models import Ambiente


class AmbienteSerializer(serializers.ModelSerializer):
    status_atual = serializers.SerializerMethodField()

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
            "status_atual",
            "criado_em",
            "atualizado_em",
        ]

    def get_status_atual(self, obj) -> str:
        from django.utils import timezone

        agora = timezone.now()
        em_uso = obj.reservas.filter(status="confirmada", data_inicio__lte=agora, data_fim__gte=agora).exists()
        return "ocupado" if em_uso else "livre"
