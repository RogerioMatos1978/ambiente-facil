"""Permissões RBAC compartilhadas entre os apps."""

from rest_framework.permissions import SAFE_METHODS, BasePermission


class IsAdmin(BasePermission):
    """Permite acesso apenas a usuários com papel Administrador."""

    message = "Apenas administradores podem executar esta ação."

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.is_admin)


class IsAdminOrReadOnly(BasePermission):
    """Leitura liberada para qualquer usuário autenticado; escrita apenas para administradores."""

    message = "Apenas administradores podem criar, editar ou excluir este recurso."

    def has_permission(self, request, view):
        if not (request.user and request.user.is_authenticated):
            return False
        if request.method in SAFE_METHODS:
            return True
        return request.user.is_admin


class IsOwnerOrAdmin(BasePermission):
    """Permite que o dono do recurso (ou um administrador) edite/exclua o objeto."""

    message = "Você só pode gerenciar suas próprias reservas."

    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return True
        if request.user.is_admin:
            return True
        owner = getattr(obj, "usuario", None) or getattr(obj, "solicitante", None)
        return owner == request.user
