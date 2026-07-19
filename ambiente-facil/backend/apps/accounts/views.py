from django.contrib.auth import get_user_model
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView

from apps.common.permissions import IsAdmin

from .serializers import MeuTokenObtainPairSerializer, UserCreateSerializer, UserSerializer

User = get_user_model()


class MeuTokenObtainPairView(TokenObtainPairView):
    """Endpoint de login. Aplica rate limit via throttle scope 'auth'."""

    serializer_class = MeuTokenObtainPairSerializer
    throttle_scope = "auth"


class UserViewSet(viewsets.ModelViewSet):
    """CRUD de usuários.

    Somente administradores podem gerenciar (listar todos, criar, editar, excluir).
    Qualquer usuário autenticado pode consultar a própria conta em GET /users/me/.
    """

    queryset = User.objects.all().order_by("first_name")
    filterset_fields = ["papel", "ativo_institucional", "departamento"]
    search_fields = ["first_name", "last_name", "username", "telefone"]

    def get_serializer_class(self):
        if self.action == "create":
            return UserCreateSerializer
        return UserSerializer

    def get_permissions(self):
        if self.action == "me":
            return [IsAuthenticated()]
        return [IsAdmin()]

    @action(detail=False, methods=["get"])
    def me(self, request):
        serializer = UserSerializer(request.user)
        return Response(serializer.data)
