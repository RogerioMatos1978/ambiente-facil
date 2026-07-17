"""Publica eventos em tempo real no grupo do painel sempre que uma reserva muda de estado."""

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from apps.reservations.models import Reserva


def _publicar_evento(ambiente_id, evento, dados_extra=None):
    channel_layer = get_channel_layer()
    if channel_layer is None:
        return
    payload = {"tipo": evento, "ambiente_id": ambiente_id, **(dados_extra or {})}
    async_to_sync(channel_layer.group_send)(
        "painel_ambientes",
        {"type": "ambiente_atualizado", "payload": payload},
    )


@receiver(post_save, sender=Reserva)
def notificar_reserva_salva(sender, instance: Reserva, created, **kwargs):
    evento = "reserva_criada" if created else "reserva_atualizada"
    _publicar_evento(
        instance.ambiente_id,
        evento,
        {
            "reserva_id": instance.id,
            "status": instance.status,
            "data_inicio": instance.data_inicio.isoformat(),
            "data_fim": instance.data_fim.isoformat(),
        },
    )


@receiver(post_delete, sender=Reserva)
def notificar_reserva_removida(sender, instance: Reserva, **kwargs):
    _publicar_evento(instance.ambiente_id, "reserva_removida", {"reserva_id": instance.id})
