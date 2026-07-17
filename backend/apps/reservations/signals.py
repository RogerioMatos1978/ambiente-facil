"""Dispara notificações automáticas por e-mail quando uma reserva é criada, confirmada ou cancelada."""

from django.db.models.signals import post_save
from django.dispatch import receiver

from apps.notifications.services import enviar_email_reserva

from .models import Reserva, StatusReserva


@receiver(post_save, sender=Reserva)
def enviar_notificacao_email(sender, instance: Reserva, created, **kwargs):
    if created:
        evento = "criada"
    elif instance.status == StatusReserva.CANCELADA:
        evento = "cancelada"
    elif instance.status == StatusReserva.CONFIRMADA:
        evento = "confirmada"
    else:
        return
    enviar_email_reserva(instance, evento)
