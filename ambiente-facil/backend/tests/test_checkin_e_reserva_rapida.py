"""Testes das novas features: check-in/no-show automático e reserva rápida (+ QR code)."""

from datetime import timedelta

import pytest
from django.core.management import call_command
from django.utils import timezone

from apps.reservations.models import Reserva, StatusReserva

from .utils_tempo import horario_futuro, horario_passado

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

    inicio = horario_futuro()
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

    inicio = horario_passado()
    passada = Reserva.objects.create(
        ambiente=ambiente, solicitante=usuario_comum, titulo="Aula encerrada",
        data_inicio=inicio, data_fim=inicio + timedelta(hours=1),
    )
    futura_inicio = horario_futuro()
    futura = Reserva.objects.create(
        ambiente=ambiente, solicitante=usuario_comum, titulo="Aula futura",
        data_inicio=futura_inicio, data_fim=futura_inicio + timedelta(hours=1),
    )

    call_command("concluir_reservas_passadas")

    passada.refresh_from_db()
    futura.refresh_from_db()
    assert passada.status == StatusReserva.CONCLUIDA
    assert futura.status == StatusReserva.CONFIRMADA


def test_mensagem_e_link_whatsapp_incluem_numero_controle_e_abrem_app(ambiente, usuario_comum):
    from apps.notifications.services import montar_link_whatsapp, montar_mensagem_whatsapp

    usuario_comum.telefone = "62999998888"
    usuario_comum.save()

    inicio = horario_futuro()
    reserva = Reserva.objects.create(
        ambiente=ambiente, solicitante=usuario_comum, titulo="Reunião",
        data_inicio=inicio, data_fim=inicio + timedelta(hours=1),
    )

    mensagem = montar_mensagem_whatsapp(reserva)
    assert reserva.numero_controle in mensagem
    assert mensagem.startswith("Olá")
    assert "retire a chave" in mensagem.lower()
    assert "guarita" in mensagem.lower()

    dados = montar_link_whatsapp(reserva)
    assert dados["link"].startswith("https://wa.me/")
    assert reserva.numero_controle in dados["mensagem"]
    # Sem reservado_para_telefone preenchido, cai para o telefone do solicitante.
    assert dados["telefone"] == "5562999998888"


def test_mensagem_whatsapp_vai_para_reservado_para_quando_preenchido(ambiente, usuario_comum):
    from apps.notifications.services import montar_link_whatsapp

    usuario_comum.telefone = "62999998888"
    usuario_comum.save()

    inicio = horario_futuro()
    reserva = Reserva.objects.create(
        ambiente=ambiente, solicitante=usuario_comum, titulo="Aula com instrutor",
        data_inicio=inicio, data_fim=inicio + timedelta(hours=1),
        reservado_para_categoria="instrutor", reservado_para_nome="Carlos Instrutor",
        reservado_para_telefone="62911112222",
    )

    dados = montar_link_whatsapp(reserva)
    assert dados["telefone"] == "5562911112222"
    assert "Carlos Instrutor" in dados["mensagem"]


def test_link_whatsapp_usa_wa_me(ambiente, usuario_comum):
    from apps.notifications.services import montar_link_whatsapp

    usuario_comum.telefone = "62999998888"
    usuario_comum.save()
    inicio = horario_futuro()
    reserva = Reserva.objects.create(
        ambiente=ambiente, solicitante=usuario_comum, titulo="Reunião",
        data_inicio=inicio, data_fim=inicio + timedelta(hours=1),
    )
    dados = montar_link_whatsapp(reserva)
    assert dados["link"].startswith("https://wa.me/")
    assert "whatsapp://" not in dados["link"]


def test_endpoint_whatsapp_bloqueado_fora_de_confirmada(cliente_autenticado_usuario, ambiente, usuario_comum):
    from django.urls import reverse

    inicio = horario_futuro()
    reserva = Reserva.objects.create(
        ambiente=ambiente, solicitante=usuario_comum, titulo="Pendente",
        data_inicio=inicio, data_fim=inicio + timedelta(hours=1), status=StatusReserva.PENDENTE,
    )
    url = reverse("reserva-whatsapp", kwargs={"pk": reserva.id})
    response = cliente_autenticado_usuario.get(url)
    assert response.status_code == 400


def test_endpoint_whatsapp_funciona_para_confirmada(cliente_autenticado_usuario, ambiente, usuario_comum):
    from django.urls import reverse

    usuario_comum.telefone = "62999998888"
    usuario_comum.save()
    inicio = horario_futuro()
    reserva = Reserva.objects.create(
        ambiente=ambiente, solicitante=usuario_comum, titulo="Confirmada",
        data_inicio=inicio, data_fim=inicio + timedelta(hours=1), status=StatusReserva.CONFIRMADA,
    )
    url = reverse("reserva-whatsapp", kwargs={"pk": reserva.id})
    response = cliente_autenticado_usuario.get(url)
    assert response.status_code == 200
    assert response.data["link"].startswith("https://wa.me/")
