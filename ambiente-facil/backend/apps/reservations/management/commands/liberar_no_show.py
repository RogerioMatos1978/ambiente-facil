"""
Libera automaticamente reservas cujo check-in não foi confirmado dentro da
tolerância configurada no ambiente (no-show), evitando salas "fantasma"
marcadas como ocupadas sem ninguém usando.

Roda periodicamente em segundo plano (ver apps/reservations/apps.py, que
agenda esta execução via APScheduler quando NO_SHOW_SCHEDULER_ATIVO=True),
mas também pode ser executado manualmente:

    python manage.py liberar_no_show
"""

from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.audit.models import AcaoAuditoria, registrar
from apps.reservations.models import Reserva, StatusReserva


class Command(BaseCommand):
    help = "Libera automaticamente reservas com check-in pendente além da tolerância (no-show)."

    def handle(self, *args, **options):
        agora = timezone.now()

        candidatas = Reserva.objects.select_related("ambiente").filter(
            status=StatusReserva.CONFIRMADA,
            checkin_confirmado_em__isnull=True,
            ambiente__exige_checkin=True,
            data_inicio__lte=agora,
            data_fim__gt=agora,
        )

        liberadas = 0
        for reserva in candidatas:
            if not reserva.checkin_expirado(agora):
                continue

            reserva.status = StatusReserva.EXPIRADA
            reserva.motivo_cancelamento = "Liberada automaticamente: check-in não confirmado (no-show)."
            reserva.cancelado_em = agora
            reserva.save()

            registrar(
                None,
                AcaoAuditoria.CANCELAMENTO,
                "Reserva",
                reserva.id,
                descricao=f"Reserva '{reserva.titulo}' liberada automaticamente por no-show.",
                detalhes={"motivo": reserva.motivo_cancelamento},
            )
            liberadas += 1

        if liberadas:
            self.stdout.write(self.style.SUCCESS(f"{liberadas} reserva(s) liberada(s) por no-show."))
        else:
            self.stdout.write("Nenhuma reserva para liberar.")
