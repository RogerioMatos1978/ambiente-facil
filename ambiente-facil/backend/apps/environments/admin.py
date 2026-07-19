from django.contrib import admin

from .models import Ambiente


@admin.register(Ambiente)
class AmbienteAdmin(admin.ModelAdmin):
    list_display = ("nome", "tipo", "capacidade", "localizacao", "ativo", "exige_checkin")
    list_filter = ("tipo", "ativo", "exige_checkin")
    search_fields = ("nome", "localizacao")
