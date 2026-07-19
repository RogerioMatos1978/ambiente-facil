"""
Conclui automaticamente reservas cujo horário de término já passou, mas que
ainda estavam com status "pendente" ou "confirmada" (ou seja, ninguém
cancelou nem elas expiraram por no-show). Uma vez concluída, a reserva se
torna somente leitura: não é mais possível editá-la, excluí-la ou cancelá-la
(ver ReservaSerializer.validate e ReservaViewSet.cancelar).

Roda periodicamente em segundo plano (ver apps/reservations/apps.py, que
agenda esta execução via APScheduler), mas também pode ser executado
manualmente:

    python manage.py concluir_reservas_passadas
"""

from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.audit.models import AcaoAuditoria, registrar
from apps.reservations.models import Reserva, StatusReserva


class Command(BaseCommand):
    help = "Marca como concluídas as reservas pendentes/confirmadas cujo período já terminou."

    def handle(self, *args, **options):
        agora = timezone.now()

        candidatas = Reserva.objects.filter(
            status__in=[StatusReserva.PENDENTE, StatusReserva.CONFIRMADA],
            data_fim__lte=agora,
        )

        concluidas = 0
        for reserva in candidatas:
            reserva.status = StatusReserva.CONCLUIDA
            reserva.save()

            registrar(
                None,
                AcaoAuditoria.ATUALIZACAO,
                "Reserva",
                reserva.id,
                descricao=f"Reserva '{reserva.titulo}' concluída automaticamente (período encerrado).",
            )
            concluidas += 1

        if concluidas:
            self.stdout.write(self.style.SUCCESS(f"{concluidas} reserva(s) marcada(s) como concluída(s)."))
        else:
            self.stdout.write("Nenhuma reserva para concluir.")
