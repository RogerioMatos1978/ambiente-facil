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
        import apps.reservations.signals  # noqa

        comando_atual = sys.argv[1] if len(sys.argv) > 1 else ""
        if comando_atual in _COMANDOS_SEM_AGENDADOR:
            return

        self._iniciar_agendador_no_show()

    def _iniciar_agendador_no_show(self):
        from django.conf import settings

        if not getattr(settings, "NO_SHOW_SCHEDULER_ATIVO", True):
            return

        from apscheduler.schedulers.background import BackgroundScheduler

        def job():
            from django.core.management import call_command

            call_command("liberar_no_show")

        intervalo = getattr(settings, "NO_SHOW_INTERVALO_MINUTOS", 5)
        scheduler = BackgroundScheduler(daemon=True, timezone=str(settings.TIME_ZONE))
        scheduler.add_job(
            job,
            "interval",
            minutes=intervalo,
            id="liberar_no_show",
            replace_existing=True,
            max_instances=1,
        )
        scheduler.start()
