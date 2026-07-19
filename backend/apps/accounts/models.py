"""Modelo de usuário customizado com papéis (RBAC) para o Ambiente Fácil."""

from django.contrib.auth.base_user import BaseUserManager
from django.contrib.auth.hashers import make_password
from django.contrib.auth.models import AbstractUser
from django.db import models
from simple_history.models import HistoricalRecords


class UserManager(BaseUserManager):
    """
    Gerenciador de usuário sem e-mail. O UserManager padrão do Django (usado
    automaticamente por AbstractUser) sempre passa `email=` para o construtor do model,
    mesmo quando não informado — o que quebra assim que o campo é removido. Este
    gerenciador reimplementa create_user/create_superuser sem essa dependência.
    """

    use_in_migrations = True

    def _create_user(self, username, password, **extra_fields):
        if not username:
            raise ValueError("É obrigatório informar o nome de usuário.")
        username = self.model.normalize_username(username)
        user = self.model(username=username, **extra_fields)
        user.password = make_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, username, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)
        return self._create_user(username, password, **extra_fields)

    def create_superuser(self, username, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superusuário precisa ter is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superusuário precisa ter is_superuser=True.")
        return self._create_user(username, password, **extra_fields)


class Papel(models.TextChoices):
    ADMINISTRADOR = "admin", "Administrador"
    USUARIO = "user", "Usuário"


class User(AbstractUser):
    """
    Usuário do sistema. Estende o usuário padrão do Django com papel (role) e dados
    institucionais. O sistema não usa e-mail: o campo herdado de AbstractUser é removido
    e o telefone (WhatsApp) é o dado de contato do usuário.
    """

    # Remove o campo email herdado de AbstractUser — o sistema não usa e-mail para nada
    # (nem login, nem notificação). REQUIRED_FIELDS também precisa ser esvaziado, pois o
    # padrão de AbstractUser é ["email"].
    email = None
    REQUIRED_FIELDS = []

    objects = UserManager()

    papel = models.CharField(max_length=10, choices=Papel.choices, default=Papel.USUARIO, verbose_name="Papel")
    telefone = models.CharField(
        max_length=20,
        blank=True,
        verbose_name="Telefone (WhatsApp)",
        help_text="Formato com DDI e DDD, ex: 5511999999999. Principal contato do usuário no sistema.",
    )
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
