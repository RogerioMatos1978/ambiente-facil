"""Testes das novas features: check-in/no-show automático e reserva rápida (+ QR code)."""

from datetime import timedelta

import pytest
from django.core.management import call_command
from django.utils import timezone

from apps.reservations.models import Reserva, StatusReserva

pytestmark = pytest.mark.django_db


@pytest.fixture
def ambiente_com_checkin(db):
    from apps.environments.models import Ambiente

    return Ambiente.objects.create(
        nome="Laboratório 1",
        tipo="laboratorio",
        capacidade=20,
        exige_checkin=True,
        tolerancia_checkin_minutos=15,
    )


def test_checkin_confirma_presenca(cliente_autenticado_usuario, usuario_comum, ambiente_com_checkin):
    inicio = timezone.now() - timedelta(minutes=5)
    fim = inicio + timedelta(hours=1)
    reserva = Reserva.objects.create(
        ambiente=ambiente_com_checkin, solicitante=usuario_comum, titulo="Aula prática",
        data_inicio=inicio, data_fim=fim,
    )
    assert reserva.precisa_checkin is True

    resposta = cliente_autenticado_usuario.post(f"/api/v1/reservations/{reserva.id}/checkin/")
    assert resposta.status_code == 200
    reserva.refresh_from_db()
    assert reserva.checkin_confirmado_em is not None
    assert reserva.precisa_checkin is False


def test_checkin_duplicado_e_rejeitado(cliente_autenticado_usuario, usuario_comum, ambiente_com_checkin):
    inicio = timezone.now() - timedelta(minutes=5)
    reserva = Reserva.objects.create(
        ambiente=ambiente_com_checkin, solicitante=usuario_comum, titulo="Aula prática",
        data_inicio=inicio, data_fim=inicio + timedelta(hours=1), checkin_confirmado_em=timezone.now(),
    )
    resposta = cliente_autenticado_usuario.post(f"/api/v1/reservations/{reserva.id}/checkin/")
    assert resposta.status_code == 400


def test_liberar_no_show_expira_reserva_sem_checkin(usuario_comum, ambiente_com_checkin):
    # Reserva começou há 20 minutos (tolerância é 15) e ninguém confirmou check-in.
    inicio = timezone.now() - timedelta(minutes=20)
    reserva = Reserva.objects.create(
        ambiente=ambiente_com_checkin, solicitante=usuario_comum, titulo="Reunião",
        data_inicio=inicio, data_fim=inicio + timedelta(hours=1),
    )

    call_command("liberar_no_show")

    reserva.refresh_from_db()
    assert reserva.status == StatusReserva.EXPIRADA
    assert "no-show" in reserva.motivo_cancelamento.lower()


def test_liberar_no_show_nao_afeta_reserva_com_checkin(usuario_comum, ambiente_com_checkin):
    inicio = timezone.now() - timedelta(minutes=20)
    reserva = Reserva.objects.create(
        ambiente=ambiente_com_checkin, solicitante=usuario_comum, titulo="Reunião",
        data_inicio=inicio, data_fim=inicio + timedelta(hours=1), checkin_confirmado_em=timezone.now(),
    )

    call_command("liberar_no_show")

    reserva.refresh_from_db()
    assert reserva.status == StatusReserva.CONFIRMADA


def test_liberar_no_show_respeita_tolerancia(usuario_comum, ambiente_com_checkin):
    # Só 5 minutos se passaram, tolerância é 15 — ainda não deve expirar.
    inicio = timezone.now() - timedelta(minutes=5)
    reserva = Reserva.objects.create(
        ambiente=ambiente_com_checkin, solicitante=usuario_comum, titulo="Reunião",
        data_inicio=inicio, data_fim=inicio + timedelta(hours=1),
    )

    call_command("liberar_no_show")

    reserva.refresh_from_db()
    assert reserva.status == StatusReserva.CONFIRMADA


def test_reserva_rapida_cria_reserva_a_partir_de_agora(cliente_autenticado_usuario, ambiente):
    resposta = cliente_autenticado_usuario.post(
        "/api/v1/reservations/rapida/", {"ambiente": ambiente.id, "duracao_minutos": 30}
    )
    assert resposta.status_code == 201
    reserva = Reserva.objects.get(id=resposta.data["id"])
    assert reserva.status == StatusReserva.CONFIRMADA
    assert (reserva.data_fim - reserva.data_inicio) == timedelta(minutes=30)


def test_reserva_rapida_respeita_conflito(cliente_autenticado_usuario, usuario_comum, ambiente):
    inicio = timezone.now()
    Reserva.objects.create(
        ambiente=ambiente, solicitante=usuario_comum, titulo="Já em andamento",
        data_inicio=inicio, data_fim=inicio + timedelta(minutes=30),
    )
    resposta = cliente_autenticado_usuario.post(
        "/api/v1/reservations/rapida/", {"ambiente": ambiente.id, "duracao_minutos": 30}
    )
    assert resposta.status_code == 400


def test_qrcode_retorna_imagem_png_sem_autenticacao(api_client, ambiente):
    resposta = api_client.get(f"/api/v1/environments/{ambiente.id}/qrcode/")
    assert resposta.status_code == 200
    assert resposta["Content-Type"] == "image/png"


def test_relatorio_retorna_resumo_e_series(cliente_autenticado_admin, ambiente, admin_user):
    from django.urls import reverse

    from apps.reservations.models import Reserva, StatusReserva

    inicio = timezone.now() + timedelta(hours=1)
    Reserva.objects.create(
        ambiente=ambiente,
        solicitante=admin_user,
        titulo="Reunião 1",
        data_inicio=inicio,
        data_fim=inicio + timedelta(hours=1),
    )
    Reserva.objects.create(
        ambiente=ambiente,
        solicitante=admin_user,
        titulo="Reunião 2",
        data_inicio=inicio + timedelta(hours=2),
        data_fim=inicio + timedelta(hours=3),
        status=StatusReserva.CANCELADA,
    )

    url = reverse("reserva-relatorio")
    response = cliente_autenticado_admin.get(url)

    assert response.status_code == 200
    dados = response.data
    assert dados["resumo"]["total"] == 2
    assert dados["resumo"]["confirmadas"] == 1
    assert dados["resumo"]["canceladas"] == 1
    assert len(dados["por_dia"]) >= 1
    assert len(dados["por_ambiente"]) == 1
    assert dados["por_ambiente"][0]["total"] == 2
    assert len(dados["por_solicitante"]) == 1


def test_relatorio_usuario_comum_nao_ve_solicitantes(cliente_autenticado_usuario):
    from django.urls import reverse

    url = reverse("reserva-relatorio")
    response = cliente_autenticado_usuario.get(url)

    assert response.status_code == 200
    assert response.data["por_solicitante"] == []


def test_concluir_reservas_passadas_marca_como_concluida(ambiente, usuario_comum):
    from django.core.management import call_command

    from apps.reservations.models import Reserva, StatusReserva

    inicio = timezone.now() - timedelta(hours=3)
    passada = Reserva.objects.create(
        ambiente=ambiente, solicitante=usuario_comum, titulo="Aula encerrada",
        data_inicio=inicio, data_fim=inicio + timedelta(hours=1),
    )
    futura_inicio = timezone.now() + timedelta(hours=1)
    futura = Reserva.objects.create(
        ambiente=ambiente, solicitante=usuario_comum, titulo="Aula futura",
        data_inicio=futura_inicio, data_fim=futura_inicio + timedelta(hours=1),
    )

    call_command("concluir_reservas_passadas")

    passada.refresh_from_db()
    futura.refresh_from_db()
    assert passada.status == StatusReserva.CONCLUIDA
    assert futura.status == StatusReserva.CONFIRMADA
