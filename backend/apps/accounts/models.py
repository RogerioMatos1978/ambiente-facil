"""Modelo de usuário customizado com papéis (RBAC) para o Ambiente Fácil."""

from django.contrib.auth.models import AbstractUser
from django.db import models
from simple_history.models import HistoricalRecords


class Papel(models.TextChoices):
    ADMINISTRADOR = "admin", "Administrador"
    USUARIO = "user", "Usuário"


class User(AbstractUser):
    """Usuário do sistema. Estende o usuário padrão do Django com papel (role) e dados institucionais."""

    papel = models.CharField(max_length=10, choices=Papel.choices, default=Papel.USUARIO, verbose_name="Papel")
    telefone = models.CharField(max_length=20, blank=True, help_text="Formato com DDI e DDD, ex: 5511999999999")
    departamento = models.CharField(max_length=120, blank=True)
    ativo_institucional = models.BooleanField(default=True, verbose_name="Ativo na instituição")
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    # Campos preparados para integrações futuras (LDAP/AD, Microsoft 365, Google)
    identificador_externo = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text="ID do usuário em um provedor externo (LDAP/AD, Azure AD, Google Workspace).",
    )
    provedor_externo = models.CharField(
        max_length=30,
        blank=True,
        null=True,
        help_text="Ex.: 'ldap', 'azure_ad', 'google_workspace'.",
    )

    history = HistoricalRecords()

    class Meta:
        verbose_name = "Usuário"
        verbose_name_plural = "Usuários"
        ordering = ["first_name", "last_name"]

    def __str__(self):
        return self.get_full_name() or self.username

    @property
    def is_admin(self) -> bool:
        return self.papel == Papel.ADMINISTRADOR or self.is_superuser

    @property
    def whatsapp_e164(self) -> str:
        """Retorna o telefone limpo (somente dígitos) para montagem do link wa.me."""
        return "".join(ch for ch in self.telefone if ch.isdigit())
