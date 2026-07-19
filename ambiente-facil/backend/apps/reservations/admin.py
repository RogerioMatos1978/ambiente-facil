from django.contrib import admin

from .models import Reserva


@admin.register(Reserva)
class ReservaAdmin(admin.ModelAdmin):
    list_display = ("titulo", "ambiente", "solicitante", "data_inicio", "data_fim", "status", "checkin_confirmado_em")
    list_filter = ("status", "ambiente")
    search_fields = ("titulo", "solicitante__username", "ambiente__nome")
