"""Testes de prevenção de conflitos de horário e regras de negócio das reservas."""

from datetime import timedelta

import pytest
from django.core.exceptions import ValidationError
from django.utils import timezone

from apps.reservations.models import Reserva, StatusReserva

pytestmark = pytest.mark.django_db


def _reserva(ambiente, solicitante, inicio, fim, **kwargs):
    return Reserva(
        ambiente=ambiente,
        solicitante=solicitante,
        titulo="Aula de teste",
        data_inicio=inicio,
        data_fim=fim,
        **kwargs,
    )


def test_criacao_reserva_valida(ambiente, usuario_comum):
    inicio = timezone.now() + timedelta(hours=1)
    fim = inicio + timedelta(hours=2)
    reserva = _reserva(ambiente, usuario_comum, inicio, fim)
    reserva.save()
    assert reserva.pk is not None
    assert reserva.status == StatusReserva.CONFIRMADA


def test_conflito_de_horario_impede_nova_reserva(ambiente, usuario_comum):
    inicio = timezone.now() + timedelta(hours=1)
    fim = inicio + timedelta(hours=2)
    _reserva(ambiente, usuario_comum, inicio, fim).save()

    conflitante = _reserva(ambiente, usuario_comum, inicio + timedelta(minutes=30), fim + timedelta(minutes=30))
    with pytest.raises(ValidationError):
        conflitante.save()


def test_reservas_nao_sobrepostas_sao_permitidas(ambiente, usuario_comum):
    inicio = timezone.now() + timedelta(hours=1)
    fim = inicio + timedelta(hours=2)
    _reserva(ambiente, usuario_comum, inicio, fim).save()

    seguinte = _reserva(ambiente, usuario_comum, fim, fim + timedelta(hours=1))
    seguinte.save()
    assert seguinte.pk is not None


def test_reserva_cancelada_nao_gera_conflito(ambiente, usuario_comum):
    inicio = timezone.now() + timedelta(hours=1)
    fim = inicio + timedelta(hours=2)
    primeira = _reserva(ambiente, usuario_comum, inicio, fim)
    primeira.save()
    primeira.status = StatusReserva.CANCELADA
    primeira.save()

    nova = _reserva(ambiente, usuario_comum, inicio, fim)
    nova.save()
    assert nova.pk is not None


def test_data_fim_antes_do_inicio_invalida(ambiente, usuario_comum):
    inicio = timezone.now() + timedelta(hours=2)
    fim = inicio - timedelta(hours=1)
    with pytest.raises(ValidationError):
        _reserva(ambiente, usuario_comum, inicio, fim).save()


def test_numero_controle_formatado_a_partir_do_id(ambiente, usuario_comum):
    inicio = timezone.now() + timedelta(hours=1)
    reserva = _reserva(ambiente, usuario_comum, inicio, inicio + timedelta(hours=1))
    reserva.save()
    assert reserva.numero_controle == f"RES-{reserva.id:06d}"


def test_numero_controle_vazio_sem_id():
    from apps.reservations.models import Reserva

    reserva = Reserva()
    assert reserva.numero_controle == ""


def test_duracao_horas_e_display(ambiente, usuario_comum):
    inicio = timezone.now() + timedelta(hours=1)

    reserva_1h30 = _reserva(ambiente, usuario_comum, inicio, inicio + timedelta(hours=1, minutes=30))
    reserva_1h30.save()
    assert reserva_1h30.duracao_horas == 1.5
    assert reserva_1h30.duracao_display == "1h30min"

    reserva_2h = _reserva(
        ambiente, usuario_comum, inicio + timedelta(hours=3), inicio + timedelta(hours=5)
    )
    reserva_2h.save()
    assert reserva_2h.duracao_horas == 2.0
    assert reserva_2h.duracao_display == "2h"

    reserva_45min = _reserva(
        ambiente, usuario_comum, inicio + timedelta(hours=6), inicio + timedelta(hours=6, minutes=45)
    )
    reserva_45min.save()
    assert reserva_45min.duracao_horas == 0.75
    assert reserva_45min.duracao_display == "45min"


def test_filtro_data_de_ate_inclui_reservas_que_cruzam_a_janela(
    cliente_autenticado_admin, ambiente, admin_user
):
    """Uma reserva que começa antes da janela filtrada mas termina dentro dela (ou que
    começa dentro dela mas termina depois) precisa aparecer — não só as totalmente
    contidas no intervalo. Regressão do bug em que o calendário escondia reservas."""
    from django.urls import reverse

    from apps.reservations.models import Reserva

    base = timezone.now().replace(minute=0, second=0, microsecond=0) + timedelta(days=1)

    cruza_inicio_da_janela = Reserva.objects.create(
        ambiente=ambiente, solicitante=admin_user, titulo="Começa antes, termina dentro",
        data_inicio=base - timedelta(hours=1), data_fim=base + timedelta(hours=1),
    )
    cruza_fim_da_janela = Reserva.objects.create(
        ambiente=ambiente, solicitante=admin_user, titulo="Começa dentro, termina depois",
        data_inicio=base + timedelta(hours=5), data_fim=base + timedelta(hours=8),
    )
    totalmente_dentro = Reserva.objects.create(
        ambiente=ambiente, solicitante=admin_user, titulo="Totalmente dentro",
        data_inicio=base + timedelta(hours=2), data_fim=base + timedelta(hours=3),
    )
    totalmente_fora = Reserva.objects.create(
        ambiente=ambiente, solicitante=admin_user, titulo="Totalmente fora",
        data_inicio=base + timedelta(days=10), data_fim=base + timedelta(days=10, hours=1),
    )

    janela_de = base
    janela_ate = base + timedelta(hours=6)

    url = reverse("reserva-list")
    resposta = cliente_autenticado_admin.get(
        url, {"data_de": janela_de.isoformat(), "data_ate": janela_ate.isoformat()}
    )
    ids_retornados = {r["id"] for r in resposta.data["results"]}

    assert cruza_inicio_da_janela.id in ids_retornados
    assert cruza_fim_da_janela.id in ids_retornados
    assert totalmente_dentro.id in ids_retornados
    assert totalmente_fora.id not in ids_retornados
