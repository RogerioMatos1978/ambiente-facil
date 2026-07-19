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


def test_usuario_comum_ve_a_lista_completa_de_reservas(
    cliente_autenticado_usuario, cliente_autenticado_admin, ambiente, usuario_comum, admin_user
):
    """A agenda é compartilhada: todo usuário autenticado vê todas as reservas (de todo
    mundo), não só as próprias. Só editar/excluir/cancelar continua restrito a admin."""
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
    assert resposta_usuario.data["count"] == 2

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


def test_usuario_comum_nao_pode_cancelar_propria_reserva(cliente_autenticado_usuario, ambiente, usuario_comum):
    from apps.reservations.models import Reserva

    inicio = timezone.now() + timedelta(hours=1)
    reserva = Reserva.objects.create(
        ambiente=ambiente, solicitante=usuario_comum, titulo="Reunião",
        data_inicio=inicio, data_fim=inicio + timedelta(hours=1),
    )
    url = reverse("reserva-cancelar", kwargs={"pk": reserva.id})
    response = cliente_autenticado_usuario.post(url, {}, format="json")
    assert response.status_code == 403


def test_admin_pode_cancelar_reserva_de_qualquer_usuario(
    cliente_autenticado_admin, ambiente, usuario_comum
):
    from apps.reservations.models import Reserva, StatusReserva

    inicio = timezone.now() + timedelta(hours=1)
    reserva = Reserva.objects.create(
        ambiente=ambiente, solicitante=usuario_comum, titulo="Reunião",
        data_inicio=inicio, data_fim=inicio + timedelta(hours=1),
    )
    url = reverse("reserva-cancelar", kwargs={"pk": reserva.id})
    response = cliente_autenticado_admin.post(url, {}, format="json")
    assert response.status_code == 200
    reserva.refresh_from_db()
    assert reserva.status == StatusReserva.CANCELADA


def test_usuario_comum_nao_pode_editar_propria_reserva(cliente_autenticado_usuario, ambiente, usuario_comum):
    from apps.reservations.models import Reserva

    inicio = timezone.now() + timedelta(hours=1)
    reserva = Reserva.objects.create(
        ambiente=ambiente, solicitante=usuario_comum, titulo="Reunião",
        data_inicio=inicio, data_fim=inicio + timedelta(hours=1),
    )
    url = reverse("reserva-detail", kwargs={"pk": reserva.id})
    response = cliente_autenticado_usuario.patch(url, {"titulo": "Outro título"}, format="json")
    assert response.status_code == 403


def test_admin_nao_pode_editar_reserva_concluida(cliente_autenticado_admin, ambiente, admin_user):
    from apps.reservations.models import Reserva, StatusReserva

    inicio = timezone.now() - timedelta(hours=3)
    reserva = Reserva.objects.create(
        ambiente=ambiente, solicitante=admin_user, titulo="Reunião passada",
        data_inicio=inicio, data_fim=inicio + timedelta(hours=1), status=StatusReserva.CONCLUIDA,
    )
    url = reverse("reserva-detail", kwargs={"pk": reserva.id})
    response = cliente_autenticado_admin.patch(url, {"titulo": "Outro título"}, format="json")
    assert response.status_code == 400

    url_cancelar = reverse("reserva-cancelar", kwargs={"pk": reserva.id})
    response_cancelar = cliente_autenticado_admin.post(url_cancelar, {}, format="json")
    assert response_cancelar.status_code == 400


def test_cancelar_reserva_com_periodo_ja_encerrado_e_bloqueado(
    cliente_autenticado_admin, ambiente, admin_user
):
    from apps.reservations.models import Reserva, StatusReserva

    inicio = timezone.now() - timedelta(hours=3)
    reserva = Reserva.objects.create(
        ambiente=ambiente, solicitante=admin_user, titulo="Reunião passada",
        data_inicio=inicio, data_fim=inicio + timedelta(hours=1), status=StatusReserva.CONFIRMADA,
    )
    url = reverse("reserva-cancelar", kwargs={"pk": reserva.id})
    response = cliente_autenticado_admin.post(url, {}, format="json")
    assert response.status_code == 400


def test_outro_usuario_nao_pode_fazer_checkin_em_reserva_alheia(
    cliente_autenticado_usuario, ambiente, admin_user
):
    """A lista de reservas ficou aberta a todos, mas check-in continua exclusivo do
    próprio solicitante (ou admin) — não pode virar 'qualquer um confirma por qualquer um'."""
    from apps.environments.models import Ambiente
    from apps.reservations.models import Reserva

    ambiente_com_checkin = Ambiente.objects.create(
        nome="Sala com check-in", tipo="sala_aula", capacidade=10, exige_checkin=True
    )
    inicio = timezone.now() - timedelta(minutes=1)
    reserva = Reserva.objects.create(
        ambiente=ambiente_com_checkin, solicitante=admin_user, titulo="Reunião do admin",
        data_inicio=inicio, data_fim=inicio + timedelta(hours=1),
    )
    url = reverse("reserva-checkin", kwargs={"pk": reserva.id})
    response = cliente_autenticado_usuario.post(url, {}, format="json")
    assert response.status_code == 403
