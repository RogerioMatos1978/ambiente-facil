from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import User


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ("username", "first_name", "last_name", "email", "papel", "is_active")
    list_filter = ("papel", "is_active", "departamento")
    fieldsets = UserAdmin.fieldsets + (
        (
            "Informações institucionais",
            {
                "fields": (
                    "papel",
                    "telefone",
                    "departamento",
                    "ativo_institucional",
                    "identificador_externo",
                    "provedor_externo",
                ),
            },
        ),
    )
