import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

User = get_user_model()


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def admin_user(db):
    return User.objects.create_user(username="admin", telefone="62999990000", password="SenhaForte123", papel="admin")


@pytest.fixture
def usuario_comum(db):
    return User.objects.create_user(
        username="usuario", telefone="62988880000", password="SenhaForte123", papel="user"
    )


@pytest.fixture
def vigilante_user(db):
    return User.objects.create_user(
        username="vigilante", telefone="62977770000", password="SenhaForte123", papel="vigilante"
    )


@pytest.fixture
def cliente_autenticado_admin(admin_user):
    client = APIClient()
    client.force_authenticate(user=admin_user)
    return client


@pytest.fixture
def cliente_autenticado_usuario(usuario_comum):
    client = APIClient()
    client.force_authenticate(user=usuario_comum)
    return client


@pytest.fixture
def cliente_autenticado_vigilante(vigilante_user):
    client = APIClient()
    client.force_authenticate(user=vigilante_user)
    return client


@pytest.fixture
def ambiente(db):
    from apps.environments.models import Ambiente

    return Ambiente.objects.create(nome="Sala 101", tipo="sala_aula", capacidade=40)
