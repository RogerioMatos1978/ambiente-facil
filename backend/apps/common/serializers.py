from rest_framework import serializers

from .models import ConfiguracaoSistema


class ConfiguracaoSistemaSerializer(serializers.ModelSerializer):
    class Meta:
        model = ConfiguracaoSistema
        fields = ["estilo_icone", "atualizado_em"]
        read_only_fields = ["atualizado_em"]
