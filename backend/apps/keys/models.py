"""Guarita de Chaves: controle físico da chave de cada ambiente, amarrado às reservas
do dia. Perfis com acesso: administrador (tudo) e vigilante (retirar/devolver — ver
apps.common.permissions e apps.keys.views). Não existe ação "repor": devolver já deixa
a chave disponível de novo, para qualquer perfil, sem etapa manual extra."""

from django.conf import settings
from django.db import models


class StatusChave(models.TextChoices):
    DISPONIVEL = "disponivel", "Disponível"
    OCUPADA = "ocupada", "Ocupada"


class Chave(models.Model):
    """
    Uma chave por ambiente (criada automaticamente — ver ChaveViewSet.get_queryset).
    Ciclo de vida — só dois estados, sem etapa intermediária:

        disponível --(retirar, vinculando a uma reserva do dia)--> ocupada
        ocupada --(devolver)--> disponível
            (a própria ação "devolver" já encerra a reserva vinculada e libera a sala)
    """

    ambiente = models.OneToOneField("environments.Ambiente", on_delete=models.CASCADE, related_name="chave")
    status = models.CharField(max_length=20, choices=StatusChave.choices, default=StatusChave.DISPONIVEL)

    reserva_atual = models.ForeignKey(
        "reservations.Reserva",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="+",
        help_text="Reserva vinculada ao ciclo de retirada/devolução em andamento.",
    )
    retirada_em = models.DateTimeField(null=True, blank=True)
    retirada_por = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="+"
    )
    devolvida_em = models.DateTimeField(null=True, blank=True)

    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Chave"
        verbose_name_plural = "Chaves"
        ordering = ["ambiente__nome"]

    def __str__(self):
        return f"Chave de {self.ambiente.nome}"
