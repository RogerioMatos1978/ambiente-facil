"""Guarita de Chaves: controle físico da chave de cada ambiente, amarrado às reservas
do dia. Perfis com acesso: administrador (tudo) e vigilante (retirar/devolver/repor —
ver apps.common.permissions e apps.keys.views)."""

from django.conf import settings
from django.db import models


class StatusChave(models.TextChoices):
    DISPONIVEL = "disponivel", "Disponível"
    OCUPADA = "ocupada", "Ocupada"
    DEVOLVIDA = "devolvida", "Devolvida"


class Chave(models.Model):
    """
    Uma chave por ambiente (criada automaticamente — ver ChaveViewSet.get_queryset).
    Ciclo de vida normal:

        disponível --(retirar, vinculando a uma reserva do dia)--> ocupada
        ocupada --(devolver)--> disponível
            (a própria ação "devolver" já encerra a reserva vinculada e libera a sala)

    "repor" continua existindo só como ajuste manual de administrador, para o caso raro
    de uma chave ficar parada em "devolvida" (ex.: edição direta via PATCH).
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
    atraso_notificado_em = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Quando o alerta de chave não devolvida foi enviado ao vigilante (evita reenvio repetido).",
    )

    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Chave"
        verbose_name_plural = "Chaves"
        ordering = ["ambiente__nome"]

    def __str__(self):
        return f"Chave de {self.ambiente.nome}"
