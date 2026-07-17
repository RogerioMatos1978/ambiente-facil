"""Testes de API cobrindo RBAC (admin x usuário comum) e autenticação JWT."""

from datetime import timedelta

import pytest
from django.urls import reverse
from django.utils import timezone

pytestmark = pytest.mark.django_db


def test_login_retorna_tokens(api_client, usuario_comum):
    url = reverse("token_obtain_pair")
    response = api_client.post(url, {"username": "usuario", "password": "SenhaForte123"}, format="json")
    assert response.status_code == 200
    assert "access" in response.data
    assert "refresh" in response.data


def test_usuario_comum_nao_pode_criar_ambiente(cliente_autenticado_usuario):
    url = reverse("ambiente-list")
    response = cliente_autenticado_usuario.post(
        url, {"nome": "Lab 2", "tipo": "laboratorio", "capacidade": 20}, format="json"
    )
    assert response.status_code == 403


def test_admin_pode_criar_ambiente(cliente_autenticado_admin):
    url = reverse("ambiente-list")
    response = cliente_autenticado_admin.post(
        url, {"nome": "Lab 2", "tipo": "laboratorio", "capacidade": 20}, format="json"
    )
    assert response.status_code == 201


def test_usuario_ve_apenas_suas_proprias_reservas(
    cliente_autenticado_usuario, cliente_autenticado_admin, ambiente, usuario_comum, admin_user
):
    from apps.reservations.models import Reserva

    inicio = timezone.now() + timedelta(hours=1)
    Reserva.objects.create(
        ambiente=ambiente,
        solicitante=usuario_comum,
        titulo="Reunião A",
        data_inicio=inicio,
        data_fim=inicio + timedelta(hours=1),
    )
    Reserva.objects.create(
        ambiente=ambiente,
        solicitante=admin_user,
        titulo="Reunião B",
        data_inicio=inicio + timedelta(hours=2),
        data_fim=inicio + timedelta(hours=3),
    )

    url = reverse("reserva-list")
    resposta_usuario = cliente_autenticado_usuario.get(url)
    assert resposta_usuario.data["count"] == 1

    resposta_admin = cliente_autenticado_admin.get(url)
    assert resposta_admin.data["count"] == 2


def test_conflito_de_horario_via_api(cliente_autenticado_usuario, ambiente, usuario_comum):
    from apps.reservations.models import Reserva

    inicio = timezone.now() + timedelta(hours=1)
    Reserva.objects.create(
        ambiente=ambiente,
        solicitante=usuario_comum,
        titulo="Reunião existente",
        data_inicio=inicio,
        data_fim=inicio + timedelta(hours=2),
    )
    url = reverse("reserva-list")
    payload = {
        "ambiente": ambiente.id,
        "titulo": "Reunião conflitante",
        "data_inicio": (inicio + timedelta(minutes=30)).isoformat(),
        "data_fim": (inicio + timedelta(hours=3)).isoformat(),
    }
    response = cliente_autenticado_usuario.post(url, payload, format="json")
    assert response.status_code == 400
    assert "conflito" in response.data["detalhes"]
