"""Testes das regras mais recentes: janela de horário (07:00–22:00), campo
"reservado para" obrigatório, mensagem da guarita e bloqueio do perfil Vigilante."""

from datetime import timedelta

import pytest
from django.core.exceptions import ValidationError
from django.urls import reverse
from django.utils import timezone

from apps.reservations.models import Reserva

from .utils_tempo import horario_futuro

pytestmark = pytest.mark.django_db


def _horario_invalido_antes_das_7():
    base = (timezone.localtime() + timedelta(days=1)).replace(hour=6, minute=30, second=0, microsecond=0)
    return base


def _horario_invalido_depois_das_22():
    base = (timezone.localtime() + timedelta(days=1)).replace(hour=21, minute=0, second=0, microsecond=0)
    return base


def test_reserva_antes_das_7h_e_invalida(ambiente, usuario_comum):
    inicio = _horario_invalido_antes_das_7()
    reserva = Reserva(
        ambiente=ambiente, solicitante=usuario_comum, titulo="Muito cedo",
        data_inicio=inicio, data_fim=inicio + timedelta(hours=1),
    )
    with pytest.raises(ValidationError):
        reserva.save()


def test_reserva_depois_das_22h_e_invalida(ambiente, usuario_comum):
    inicio = _horario_invalido_depois_das_22()
    reserva = Reserva(
        ambiente=ambiente, solicitante=usuario_comum, titulo="Termina tarde demais",
        data_inicio=inicio, data_fim=inicio + timedelta(hours=2),
    )
    with pytest.raises(ValidationError):
        reserva.save()


def test_reserva_atravessando_meia_noite_e_invalida(ambiente, usuario_comum):
    inicio = horario_futuro().replace(hour=21, minute=0)
    reserva = Reserva(
        ambiente=ambiente, solicitante=usuario_comum, titulo="Vira o dia",
        data_inicio=inicio, data_fim=inicio + timedelta(hours=2),
    )
    with pytest.raises(ValidationError):
        reserva.save()


def test_reserva_dentro_da_janela_e_valida(ambiente, usuario_comum):
    inicio = horario_futuro().replace(hour=7, minute=0)
    reserva = Reserva(
        ambiente=ambiente, solicitante=usuario_comum, titulo="Cedinho, dentro da janela",
        data_inicio=inicio, data_fim=inicio.replace(hour=22, minute=0),
    )
    reserva.save()
    assert reserva.pk is not None


def test_criar_reserva_via_api_sem_reservado_para_e_rejeitado(cliente_autenticado_usuario, ambiente):
    inicio = horario_futuro()
    url = reverse("reserva-list")
    payload = {
        "ambiente": ambiente.id,
        "titulo": "Reunião sem reservado_para",
        "data_inicio": inicio.isoformat(),
        "data_fim": (inicio + timedelta(hours=1)).isoformat(),
    }
    response = cliente_autenticado_usuario.post(url, payload, format="json")
    assert response.status_code == 400
    assert "reservado_para_categoria" in response.data["detalhes"]
    assert "reservado_para_nome" in response.data["detalhes"]
    assert "reservado_para_telefone" in response.data["detalhes"]


def test_criar_reserva_via_api_com_reservado_para_funciona(cliente_autenticado_usuario, ambiente):
    inicio = horario_futuro()
    url = reverse("reserva-list")
    payload = {
        "ambiente": ambiente.id,
        "titulo": "Aula com instrutor externo",
        "data_inicio": inicio.isoformat(),
        "data_fim": (inicio + timedelta(hours=1)).isoformat(),
        "reservado_para_categoria": "instrutor",
        "reservado_para_nome": "Maria Souza",
        "reservado_para_telefone": "62999991111",
    }
    response = cliente_autenticado_usuario.post(url, payload, format="json")
    assert response.status_code == 201
    assert response.data["reservado_para_categoria"] == "instrutor"
    assert response.data["reservado_para_nome"] == "Maria Souza"
    assert "chave" in response.data["mensagem_guarita"].lower()
    assert "devolva" in response.data["mensagem_guarita"].lower()


def test_reserva_rapida_preenche_reservado_para_automaticamente(cliente_autenticado_usuario, ambiente, usuario_comum):
    url = reverse("reserva-rapida")
    response = cliente_autenticado_usuario.post(url, {"ambiente": ambiente.id, "duracao_minutos": 30}, format="json")
    assert response.status_code == 201
    assert response.data["reservado_para_nome"] == usuario_comum.get_full_name() or usuario_comum.username
    assert response.data["reservado_para_categoria"] == "cliente"


def test_mensagem_guarita_menciona_ambiente_e_numero_controle(ambiente, usuario_comum):
    inicio = horario_futuro()
    reserva = Reserva.objects.create(
        ambiente=ambiente, solicitante=usuario_comum, titulo="Aula",
        data_inicio=inicio, data_fim=inicio + timedelta(hours=1),
        reservado_para_categoria="professor", reservado_para_nome="João Lima",
        reservado_para_telefone="62999992222",
    )
    mensagem = reserva.mensagem_guarita
    assert ambiente.nome in mensagem
    assert reserva.numero_controle in mensagem
    assert "João Lima" in mensagem
    assert "guarita" in mensagem.lower()


def test_vigilante_nao_acessa_reservas(cliente_autenticado_vigilante):
    url = reverse("reserva-list")
    response = cliente_autenticado_vigilante.get(url)
    assert response.status_code == 403


def test_vigilante_nao_acessa_ambientes(cliente_autenticado_vigilante):
    url = reverse("ambiente-list")
    response = cliente_autenticado_vigilante.get(url)
    assert response.status_code == 403


def test_usuario_comum_nao_acessa_guarita_chaves(cliente_autenticado_usuario, ambiente):
    url = reverse("chave-list")
    response = cliente_autenticado_usuario.get(url)
    assert response.status_code == 403
