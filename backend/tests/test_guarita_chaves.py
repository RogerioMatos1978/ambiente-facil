"""Testes da Guarita de Chaves: provisionamento automático, ciclo retirar/devolver/
repor amarrado a reservas do dia, e permissões (admin + vigilante only)."""

from datetime import timedelta

import pytest
from django.urls import reverse

from apps.keys.models import Chave, StatusChave
from apps.reservations.models import Reserva

from .utils_tempo import horario_futuro

pytestmark = pytest.mark.django_db


def _reserva_hoje(ambiente, solicitante, inicio_hora=9):
    from django.utils import timezone

    # "Hoje" às `inicio_hora` (por padrão 9h) — pode já ter passado no relógio real,
    # e não tem problema: reservas_hoje mostra o dia inteiro, passado ou futuro (ver
    # ChaveSerializer.get_reservas_hoje), então a guarita consegue reconciliar chaves
    # mesmo depois do horário da reserva.
    inicio = timezone.localtime().replace(hour=inicio_hora, minute=0, second=0, microsecond=0)
    return Reserva.objects.create(
        ambiente=ambiente, solicitante=solicitante, titulo="Reserva de hoje",
        data_inicio=inicio, data_fim=inicio + timedelta(hours=1),
        reservado_para_categoria="professor", reservado_para_nome="Ana Paula",
        reservado_para_telefone="62999993333",
    )


def test_chave_e_provisionada_automaticamente(cliente_autenticado_admin, ambiente):
    url = reverse("chave-list")
    response = cliente_autenticado_admin.get(url)
    assert response.status_code == 200
    assert Chave.objects.filter(ambiente=ambiente).exists()
    chave = Chave.objects.get(ambiente=ambiente)
    assert chave.status == StatusChave.DISPONIVEL


def test_vigilante_ve_reservas_de_hoje_no_ambiente(cliente_autenticado_vigilante, ambiente, usuario_comum):
    reserva = _reserva_hoje(ambiente, usuario_comum)
    url = reverse("chave-detail", kwargs={"ambiente_id": ambiente.id})
    response = cliente_autenticado_vigilante.get(url)
    assert response.status_code == 200
    ids = {r["id"] for r in response.data["reservas_hoje"]}
    assert reserva.id in ids
    assert response.data["reservas_hoje"][0]["reservado_para_nome"] == "Ana Paula"


def test_vigilante_pode_retirar_devolver_e_repor_chave(cliente_autenticado_vigilante, ambiente, usuario_comum):
    reserva = _reserva_hoje(ambiente, usuario_comum)

    url_retirar = reverse("chave-retirar", kwargs={"ambiente_id": ambiente.id})
    resp_retirar = cliente_autenticado_vigilante.post(url_retirar, {"reserva": reserva.id}, format="json")
    assert resp_retirar.status_code == 200
    assert resp_retirar.data["status"] == "ocupada"
    assert resp_retirar.data["reserva_atual"] == reserva.id

    url_devolver = reverse("chave-devolver", kwargs={"ambiente_id": ambiente.id})
    resp_devolver = cliente_autenticado_vigilante.post(url_devolver, {}, format="json")
    assert resp_devolver.status_code == 200
    assert resp_devolver.data["status"] == "devolvida"

    url_repor = reverse("chave-repor", kwargs={"ambiente_id": ambiente.id})
    resp_repor = cliente_autenticado_vigilante.post(url_repor, {}, format="json")
    assert resp_repor.status_code == 200
    assert resp_repor.data["status"] == "disponivel"
    assert resp_repor.data["reserva_atual"] is None


def test_nao_pode_retirar_chave_ja_ocupada(cliente_autenticado_vigilante, ambiente, usuario_comum):
    reserva = _reserva_hoje(ambiente, usuario_comum)
    url_retirar = reverse("chave-retirar", kwargs={"ambiente_id": ambiente.id})
    cliente_autenticado_vigilante.post(url_retirar, {"reserva": reserva.id}, format="json")

    outra_resposta = cliente_autenticado_vigilante.post(url_retirar, {"reserva": reserva.id}, format="json")
    assert outra_resposta.status_code == 400


def test_retirar_sem_reserva_valida_e_rejeitado(cliente_autenticado_vigilante, ambiente):
    url_retirar = reverse("chave-retirar", kwargs={"ambiente_id": ambiente.id})
    response = cliente_autenticado_vigilante.post(url_retirar, {"reserva": 99999}, format="json")
    assert response.status_code == 400


def test_admin_pode_editar_status_diretamente_vigilante_nao_pode(
    cliente_autenticado_admin, cliente_autenticado_vigilante, ambiente
):
    cliente_autenticado_admin.get(reverse("chave-list"))  # garante provisionamento
    url = reverse("chave-detail", kwargs={"ambiente_id": ambiente.id})

    resp_vigilante = cliente_autenticado_vigilante.patch(url, {"status": "ocupada"}, format="json")
    assert resp_vigilante.status_code == 403

    resp_admin = cliente_autenticado_admin.patch(url, {"status": "ocupada"}, format="json")
    assert resp_admin.status_code == 200
    assert resp_admin.data["status"] == "ocupada"
