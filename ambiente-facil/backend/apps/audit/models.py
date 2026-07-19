"""Registro de auditoria de ações relevantes (login, criação, cancelamento, exportação etc.)."""

from django.conf import settings
from django.db import models


class AcaoAuditoria(models.TextChoices):
    LOGIN = "login", "Login"
    LOGOUT = "logout", "Logout"
    CRIACAO = "criacao", "Criação"
    ATUALIZACAO = "atualizacao", "Atualização"
    CANCELAMENTO = "cancelamento", "Cancelamento"
    EXCLUSAO = "exclusao", "Exclusão"
    EXPORTACAO = "exportacao", "Exportação"


class LogAuditoria(models.Model):
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="logs_auditoria"
    )
    acao = models.CharField(max_length=20, choices=AcaoAuditoria.choices)
    entidade = models.CharField(max_length=100, help_text="Nome do modelo/entidade afetada, ex.: 'Reserva'.")
    entidade_id = models.CharField(max_length=50, blank=True, null=True)
    descricao = models.CharField(max_length=255, blank=True)
    detalhes = models.JSONField(default=dict, blank=True)
    endereco_ip = models.GenericIPAddressField(null=True, blank=True)
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Log de Auditoria"
        verbose_name_plural = "Logs de Auditoria"
        ordering = ["-criado_em"]

    def __str__(self):
        return f"[{self.criado_em:%d/%m/%Y %H:%M}] {self.usuario} - {self.acao} - {self.entidade}"


def registrar(usuario, acao, entidade, entidade_id=None, descricao="", detalhes=None, request=None):
    """Função utilitária para registrar um evento de auditoria a partir de qualquer parte do sistema."""
    ip = None
    if request is not None:
        xff = request.META.get("HTTP_X_FORWARDED_FOR")
        ip = xff.split(",")[0].strip() if xff else request.META.get("REMOTE_ADDR")
    return LogAuditoria.objects.create(
        usuario=usuario if usuario and usuario.is_authenticated else None,
        acao=acao,
        entidade=entidade,
        entidade_id=str(entidade_id) if entidade_id is not None else None,
        descricao=descricao,
        detalhes=detalhes or {},
        endereco_ip=ip,
    )
