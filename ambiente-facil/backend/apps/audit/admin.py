from django.contrib import admin

from .models import LogAuditoria


@admin.register(LogAuditoria)
class LogAuditoriaAdmin(admin.ModelAdmin):
    list_display = ("criado_em", "usuario", "acao", "entidade", "entidade_id")
    list_filter = ("acao", "entidade")
    search_fields = ("descricao",)
    readonly_fields = [f.name for f in LogAuditoria._meta.fields]
