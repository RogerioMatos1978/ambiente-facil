"""Configurações globais do sistema (diferente das preferências pessoais, que ficam
salvas no navegador de cada usuário — ver `frontend/src/store/tema-cor.ts`)."""

from django.db import models


class EstiloIcone(models.TextChoices):
    PADRAO = "padrao", "Padrão (contorno)"
    CONTORNADO = "contornado", "Contornado"
    PREENCHIDO = "preenchido", "Preenchido"


class ConfiguracaoSistema(models.Model):
    """
    Configuração única (singleton, sempre pk=1) válida para todos os usuários do
    sistema — ex.: o estilo visual dos ícones do menu de navegação. Só pode ser
    alterada por administradores (ver `apps.common.permissions.IsAdminOrReadOnly`);
    qualquer usuário autenticado pode lê-la.
    """

    estilo_icone = models.CharField(max_length=20, choices=EstiloIcone.choices, default=EstiloIcone.PADRAO)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Configuração do sistema"
        verbose_name_plural = "Configurações do sistema"

    def __str__(self):
        return "Configuração do sistema"

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)

    @classmethod
    def obter(cls) -> "ConfiguracaoSistema":
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj
