from django.apps import AppConfig


class ReservationsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.reservations"
    verbose_name = "Reservas"

    def ready(self):
        import apps.reservations.signals  # noqa
