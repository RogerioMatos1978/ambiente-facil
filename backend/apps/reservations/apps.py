import sys

from django.apps import AppConfig

# Comandos de manejo em que NÃO queremos iniciar o agendador em segundo
# plano (evita rodar o job durante migrate/makemigrations/testes/shell etc.).
_COMANDOS_SEM_AGENDADOR = {
    "makemigrations",
    "migrate",
    "collectstatic",
    "test",
    "shell",
    "shell_plus",
    "seed_demo",
    "createsuperuser",
    "check",
}


class ReservationsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.reservations"
    verbose_name = "Reservas"

    def ready(self):
        comando_atual = sys.argv[1] if len(sys.argv) > 1 else ""
        if comando_atual in _COMANDOS_SEM_AGENDADOR:
            return

        self._iniciar_agendadores()

    def _iniciar_agendadores(self):
        """
        Inicia os jobs periódicos em segundo plano (mesmo BackgroundScheduler):
          - liberar_no_show: libera reservas com check-in pendente além da tolerância.
          - concluir_reservas_passadas: marca como concluídas reservas cujo período
            já terminou, tornando-as somente leitura.
        Ambos compartilham o mesmo intervalo/flag de ativação (NO_SHOW_SCHEDULER_ATIVO /
        NO_SHOW_INTERVALO_MINUTOS) para não exigir configuração extra no .env.
        """
        from django.conf import settings

        if not getattr(settings, "NO_SHOW_SCHEDULER_ATIVO", True):
            return

        from apscheduler.schedulers.background import BackgroundScheduler

        def job_liberar_no_show():
            from django.core.management import call_command

            call_command("liberar_no_show")

        def job_concluir_reservas_passadas():
            from django.core.management import call_command

            call_command("concluir_reservas_passadas")

        intervalo = getattr(settings, "NO_SHOW_INTERVALO_MINUTOS", 5)
        scheduler = BackgroundScheduler(daemon=True, timezone=str(settings.TIME_ZONE))
        scheduler.add_job(
            job_liberar_no_show,
            "interval",
            minutes=intervalo,
            id="liberar_no_show",
            replace_existing=True,
            max_instances=1,
        )
        scheduler.add_job(
            job_concluir_reservas_passadas,
            "interval",
            minutes=intervalo,
            id="concluir_reservas_passadas",
            replace_existing=True,
            max_instances=1,
        )
        scheduler.start()
