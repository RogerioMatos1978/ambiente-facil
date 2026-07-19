"""
Verifica chaves que passaram do horário de devolução: se uma reserva já terminou há
mais de CHAVE_TOLERANCIA_DEVOLUCAO_MINUTOS (padrão 10) minutos e a chave ainda está
"ocupada" (não foi devolvida na guarita), dispara um alerta em tempo real para quem
estiver com a tela da Guarita de Chaves aberta (o vigilante do turno logado) e marca
a chave para que a linha correspondente apareça em amarelo na lista de Reservas.

Roda periodicamente em segundo plano (ver apps/reservations/apps.py, que agenda esta
execução via APScheduler quando NO_SHOW_SCHEDULER_ATIVO=True), mas também pode ser
executado manualmente:

    python manage.py alertar_chaves_atrasadas

Não reenvia o alerta a cada execução: assim que notificada, a chave grava
`atraso_notificado_em` e só é notificada de novo se for retirada de novo (o campo é
limpo em `retirar`/`devolver` — ver apps/keys/views.py).
"""

import logging

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.conf import settings
from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.keys.models import Chave, StatusChave

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Alerta em tempo real quando uma chave não é devolvida até 10 min após o fim da reserva."

    def handle(self, *args, **options):
        agora = timezone.now()
        tolerancia = getattr(settings, "CHAVE_TOLERANCIA_DEVOLUCAO_MINUTOS", 10)

        candidatas = (
            Chave.objects.select_related("ambiente", "reserva_atual")
            .filter(
                status=StatusChave.OCUPADA,
                reserva_atual__isnull=False,
                atraso_notificado_em__isnull=True,
            )
        )

        channel_layer = get_channel_layer()
        alertadas = 0
        for chave in candidatas:
            reserva = chave.reserva_atual
            limite = reserva.data_fim + timezone.timedelta(minutes=tolerancia)
            if agora < limite:
                continue

            # Grava a marca de "já notificado" ANTES de tentar publicar o evento em tempo
            # real: mesmo que o broadcast falhe (Redis fora do ar), a chave não deve
            # continuar disparando alerta a cada execução do job, e uma falha de
            # notificação não pode travar o processamento das próximas chaves do laço.
            chave.atraso_notificado_em = agora
            chave.save(update_fields=["atraso_notificado_em"])

            if channel_layer is not None:
                try:
                    async_to_sync(channel_layer.group_send)(
                        "painel_ambientes",
                        {
                            "type": "ambiente_atualizado",
                            "payload": {
                                "tipo": "chave_atrasada",
                                "ambiente_id": chave.ambiente_id,
                                "reserva_id": reserva.id,
                                "mensagem": (
                                    f"Chave de '{chave.ambiente.nome}' não devolvida "
                                    f"({tolerancia} min após o fim da reserva Nº {reserva.numero_controle})."
                                ),
                            },
                        },
                    )
                except Exception:
                    logger.warning(
                        "Não foi possível publicar alerta de chave atrasada em tempo real "
                        "(ambiente %s) — o registro em atraso_notificado_em já foi salvo.",
                        chave.ambiente_id,
                        exc_info=True,
                    )
            alertadas += 1

        if alertadas:
            self.stdout.write(self.style.WARNING(f"{alertadas} chave(s) atrasada(s) — alerta enviado."))
        else:
            self.stdout.write("Nenhuma chave atrasada no momento.")
