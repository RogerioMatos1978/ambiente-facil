"""Publica eventos em tempo real no grupo do painel sempre que uma reserva muda de estado."""

import logging

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from apps.reservations.models import Reserva

logger = logging.getLogger(__name__)


def _publicar_evento(ambiente_id, evento, dados_extra=None):
    """
    Notificação em tempo real é "melhor esforço": se o channel layer (Redis) estiver
    fora do ar ou inacessível, isso NUNCA pode derrubar a operação de negócio que
    disparou o signal (ex.: concluir uma reserva ao devolver a chave na guarita).
    Sem este try/except, uma falha aqui propagaria pra fora de Reserva.save() — e como
    isso acontece por dentro do POST /guarita/chaves/<id>/devolver/, o vigilante veria
    um erro 500 mesmo que a reserva já tivesse sido salva no banco, ou (com o save()
    dentro de uma transação atômica) a alteração seria revertida por completo.
    """
    try:
        channel_layer = get_channel_layer()
        if channel_layer is None:
            return
        payload = {"tipo": evento, "ambiente_id": ambiente_id, **(dados_extra or {})}
        async_to_sync(channel_layer.group_send)(
            "painel_ambientes",
            {"type": "ambiente_atualizado", "payload": payload},
        )
    except Exception:
        logger.warning(
            "Não foi possível publicar evento em tempo real (%s, ambiente %s) — "
            "painel/guarita pode estar sem atualização ao vivo, mas a operação "
            "continua normalmente.",
            evento,
            ambiente_id,
            exc_info=True,
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
