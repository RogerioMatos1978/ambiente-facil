from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.translation import gettext_lazy as _

from .models import User


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    """
    UserAdmin customizado: o sistema não tem campo e-mail (removido do modelo), então os
    fieldsets padrão do Django (que referenciam "email") precisam ser totalmente
    reescritos em vez de apenas estendidos.
    """

    list_display = ("username", "first_name", "last_name", "telefone", "papel", "is_active")
    list_filter = ("papel", "is_active", "departamento")
    search_fields = ("username", "first_name", "last_name", "telefone")

    fieldsets = (
        (None, {"fields": ("username", "password")}),
        (_("Informações pessoais"), {"fields": ("first_name", "last_name", "telefone")}),
        (
            _("Informações institucionais"),
            {
                "fields": (
                    "papel",
                    "departamento",
                    "ativo_institucional",
                    "identificador_externo",
                    "provedor_externo",
                ),
            },
        ),
        (_("Permissões"), {"fields": ("is_active", "is_staff", "is_superuser", "groups", "user_permissions")}),
        (_("Datas importantes"), {"fields": ("last_login", "date_joined")}),
    )
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": ("username", "password1", "password2", "first_name", "last_name", "telefone", "papel"),
            },
        ),
    )
