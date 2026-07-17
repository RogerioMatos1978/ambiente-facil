from django.contrib import admin

from .models import Ambiente


@admin.register(Ambiente)
class AmbienteAdmin(admin.ModelAdmin):
    list_display = ("nome", "tipo", "capacidade", "localizacao", "ativo")
    list_filter = ("tipo", "ativo")
    search_fields = ("nome", "localizacao")
