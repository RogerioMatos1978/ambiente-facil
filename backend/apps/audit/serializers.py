from rest_framework import serializers

from .models import LogAuditoria


class LogAuditoriaSerializer(serializers.ModelSerializer):
    usuario_nome = serializers.CharField(source="usuario.get_full_name", read_only=True, default="")

    class Meta:
        model = LogAuditoria
        fields = [
            "id",
            "usuario",
            "usuario_nome",
            "acao",
            "entidade",
            "entidade_id",
            "descricao",
            "detalhes",
            "endereco_ip",
            "criado_em",
        ]
        read_only_fields = fields
