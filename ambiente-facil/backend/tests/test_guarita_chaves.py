"""Testes da Guarita de Chaves: provisionamento automático, ciclo retirar/devolver
amarrado a reservas do dia (sem etapa "repor" — foi removida para todos os perfis), e
permissões (admin + vigilante only)."""

from datetime import timedelta
from unittest.mock import patch

import pytest
from django.core import management
from django.urls import NoReverseMatch, reverse
from django.utils import timezone

from apps.keys.models import Chave, StatusChave
from apps.reservations.models import Reserva, StatusReserva

from .utils_tempo import horario_futuro, horario_passado

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


def test_vigilante_pode_retirar_e_devolver_chave_encerrando_reserva(
    cliente_autenticado_vigilante, ambiente, usuario_comum
):
    """Devolver já encerra a reserva e libera sala + chave num passo só — não existe
    ação "repor" para nenhum perfil."""
    reserva = _reserva_hoje(ambiente, usuario_comum)
    reserva.status = StatusReserva.CONFIRMADA
    reserva.save()

    url_retirar = reverse("chave-retirar", kwargs={"ambiente_id": ambiente.id})
    resp_retirar = cliente_autenticado_vigilante.post(url_retirar, {"reserva": reserva.id}, format="json")
    assert resp_retirar.status_code == 200
    assert resp_retirar.data["status"] == "ocupada"
    assert resp_retirar.data["reserva_atual"] == reserva.id

    url_devolver = reverse("chave-devolver", kwargs={"ambiente_id": ambiente.id})
    resp_devolver = cliente_autenticado_vigilante.post(url_devolver, {}, format="json")
    assert resp_devolver.status_code == 200
    assert resp_devolver.data["status"] == "disponivel"
    assert resp_devolver.data["reserva_atual"] is None

    reserva.refresh_from_db()
    assert reserva.status == StatusReserva.CONCLUIDA


def test_devolver_chave_ja_disponivel_e_rejeitado(cliente_autenticado_vigilante, ambiente):
    url_devolver = reverse("chave-devolver", kwargs={"ambiente_id": ambiente.id})
    response = cliente_autenticado_vigilante.post(url_devolver, {}, format="json")
    assert response.status_code == 400


def test_alertar_chaves_atrasadas_marca_e_nao_reenvia(cliente_autenticado_vigilante, ambiente, usuario_comum):
    reserva = _reserva_hoje(ambiente, usuario_comum)
    # Fim da reserva bem no passado, garantindo que já passou da tolerância de 10 min.
    reserva.data_fim = timezone.now() - timedelta(hours=2)
    reserva.save()

    url_retirar = reverse("chave-retirar", kwargs={"ambiente_id": ambiente.id})
    cliente_autenticado_vigilante.post(url_retirar, {"reserva": reserva.id}, format="json")

    chave = Chave.objects.get(ambiente=ambiente)
    assert chave.atraso_notificado_em is None

    management.call_command("alertar_chaves_atrasadas")
    chave.refresh_from_db()
    assert chave.atraso_notificado_em is not None
    primeiro_alerta = chave.atraso_notificado_em

    # Rodar de novo não deve reenviar (não atualiza o timestamp).
    management.call_command("alertar_chaves_atrasadas")
    chave.refresh_from_db()
    assert chave.atraso_notificado_em == primeiro_alerta


def test_alertar_chaves_atrasadas_ignora_dentro_da_tolerancia(cliente_autenticado_vigilante, ambiente, usuario_comum):
    reserva = _reserva_hoje(ambiente, usuario_comum)
    reserva.data_fim = timezone.now() + timedelta(minutes=30)
    reserva.save()

    url_retirar = reverse("chave-retirar", kwargs={"ambiente_id": ambiente.id})
    cliente_autenticado_vigilante.post(url_retirar, {"reserva": reserva.id}, format="json")

    management.call_command("alertar_chaves_atrasadas")
    chave = Chave.objects.get(ambiente=ambiente)
    assert chave.atraso_notificado_em is None


def test_reserva_expoe_chave_atrasada(cliente_autenticado_usuario, cliente_autenticado_vigilante, ambiente, usuario_comum):
    reserva = _reserva_hoje(ambiente, usuario_comum)
    reserva.data_fim = timezone.now() - timedelta(hours=1)
    reserva.save()

    url_retirar = reverse("chave-retirar", kwargs={"ambiente_id": ambiente.id})
    cliente_autenticado_vigilante.post(url_retirar, {"reserva": reserva.id}, format="json")

    url = reverse("reserva-detail", kwargs={"pk": reserva.id})
    response = cliente_autenticado_usuario.get(url)
    assert response.data["chave_atrasada"] is True

    url_devolver = reverse("chave-devolver", kwargs={"ambiente_id": ambiente.id})
    cliente_autenticado_vigilante.post(url_devolver, {}, format="json")

    response2 = cliente_autenticado_usuario.get(url)
    assert response2.data["chave_atrasada"] is False


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


def test_chave_e_criada_automaticamente_ao_criar_ambiente(db):
    from apps.environments.models import Ambiente

    novo_ambiente = Ambiente.objects.create(nome="Sala Nova", tipo="sala_aula", capacidade=10)
    assert Chave.objects.filter(ambiente=novo_ambiente, status=StatusChave.DISPONIVEL).exists()


def test_reserva_expoe_status_da_chave_do_ambiente(
    cliente_autenticado_usuario, cliente_autenticado_vigilante, ambiente, usuario_comum
):
    reserva = _reserva_hoje(ambiente, usuario_comum)
    url = reverse("reserva-detail", kwargs={"pk": reserva.id})
    response = cliente_autenticado_usuario.get(url)
    assert response.status_code == 200
    assert response.data["chave_status"] == "disponivel"
    assert response.data["chave_status_display"] == "Disponível"

    url_retirar = reverse("chave-retirar", kwargs={"ambiente_id": ambiente.id})
    cliente_autenticado_vigilante.post(url_retirar, {"reserva": reserva.id}, format="json")

    response2 = cliente_autenticado_usuario.get(url)
    assert response2.data["chave_status"] == "ocupada"


def test_devolver_finaliza_reserva_mesmo_se_broadcast_em_tempo_real_falhar(
    cliente_autenticado_vigilante, ambiente, usuario_comum
):
    """
    Regressão: se o channel layer (Redis) estiver indisponível no ambiente da guarita,
    a publicação do evento em tempo real (signal disparado por Reserva.save(), ver
    apps/environments/signals.py) não pode impedir a reserva de ser encerrada nem a
    chave de ser liberada — a notificação é "melhor esforço", nunca bloqueante.
    """
    reserva = _reserva_hoje(ambiente, usuario_comum)
    reserva.status = StatusReserva.CONFIRMADA
    reserva.save()

    url_retirar = reverse("chave-retirar", kwargs={"ambiente_id": ambiente.id})
    cliente_autenticado_vigilante.post(url_retirar, {"reserva": reserva.id}, format="json")

    url_devolver = reverse("chave-devolver", kwargs={"ambiente_id": ambiente.id})
    with patch("apps.environments.signals.get_channel_layer", side_effect=RuntimeError("Redis indisponível")):
        resp_devolver = cliente_autenticado_vigilante.post(url_devolver, {}, format="json")

    assert resp_devolver.status_code == 200
    assert resp_devolver.data["status"] == "disponivel"

    reserva.refresh_from_db()
    assert reserva.status == StatusReserva.CONCLUIDA

    chave = Chave.objects.get(ambiente=ambiente)
    assert chave.status == StatusChave.DISPONIVEL
    assert chave.reserva_atual is None


def test_acao_repor_foi_removida(cliente_autenticado_vigilante, ambiente):
    """A rota/ação "repor" não existe mais para nenhum perfil — nem reverse()
    encontra a URL, já que a @action correspondente foi removida do ChaveViewSet."""
    with pytest.raises(NoReverseMatch):
        reverse("chave-repor", kwargs={"ambiente_id": ambiente.id})


def test_status_devolvida_nao_e_mais_uma_opcao_valida(cliente_autenticado_admin, ambiente):
    """"devolvida" era o estado intermediário que só existia para o fluxo de "repor".
    Removida a ação, o status deixou de ser uma opção válida — mesmo para admin via
    edição direta (PATCH)."""
    cliente_autenticado_admin.get(reverse("chave-list"))  # garante provisionamento
    url = reverse("chave-detail", kwargs={"ambiente_id": ambiente.id})
    response = cliente_autenticado_admin.patch(url, {"status": "devolvida"}, format="json")
    assert response.status_code == 400


def test_reserva_com_chave_retirada_e_concluida_automaticamente_ao_passar_o_tempo(
    cliente_autenticado_vigilante, ambiente, usuario_comum
):
    """
    Invariante central: nenhuma reserva pode ficar "pendente"/"confirmada" para
    sempre. Se a chave foi retirada mas ninguém devolve na guarita, assim que o
    horário da reserva passa, o job periódico concluir_reservas_passadas (ver
    apps/reservations/management/commands/concluir_reservas_passadas.py, agendado
    junto com o job de alerta de chave atrasada) encerra a reserva de qualquer jeito —
    a chave em si continua "ocupada" (só o vigilante devolvendo fisicamente libera a
    chave), mas a agenda nunca fica aberta indefinidamente.
    """
    reserva = _reserva_hoje(ambiente, usuario_comum)
    reserva.status = StatusReserva.CONFIRMADA
    reserva.data_fim = timezone.now() - timedelta(hours=1)
    reserva.save()

    url_retirar = reverse("chave-retirar", kwargs={"ambiente_id": ambiente.id})
    cliente_autenticado_vigilante.post(url_retirar, {"reserva": reserva.id}, format="json")

    management.call_command("concluir_reservas_passadas")

    reserva.refresh_from_db()
    assert reserva.status == StatusReserva.CONCLUIDA

    # A chave física continua ocupada — só "devolver" na guarita libera de fato — mas
    # a agenda (reserva) já não está mais aberta.
    chave = Chave.objects.get(ambiente=ambiente)
    assert chave.status == StatusChave.OCUPADA
    assert chave.reserva_atual_id == reserva.id


def test_nenhuma_reserva_pendente_ou_confirmada_sobrevive_ao_fim_do_periodo(
    cliente_autenticado_vigilante, ambiente, usuario_comum
):
    """Varredura ampla da invariante pedida: crie reservas em vários estados (com e
    sem chave retirada, algumas já viradas para o passado) e confirme que, depois de
    rodar os dois jobs de fechamento, nenhuma reserva do ambiente permanece aberta
    ("pendente"/"confirmada") com o horário já encerrado. Usa horario_passado() (ontem
    10:00, ver tests/utils_tempo.py) com dois horários distintos no mesmo dia para não
    conflitar entre si nem depender de "agora" (evita flakiness perto da virada do dia
    ou do limite de 22h da janela permitida)."""
    inicio_1 = horario_passado()
    sem_chave = Reserva.objects.create(
        ambiente=ambiente, solicitante=usuario_comum, titulo="Sem chave retirada",
        data_inicio=inicio_1, data_fim=inicio_1 + timedelta(hours=1),
        status=StatusReserva.CONFIRMADA,
        reservado_para_categoria="professor", reservado_para_nome="Bia", reservado_para_telefone="62999991111",
    )
    inicio_2 = horario_passado() + timedelta(hours=3)
    com_chave_nao_devolvida = Reserva.objects.create(
        ambiente=ambiente, solicitante=usuario_comum, titulo="Com chave retirada, não devolvida a tempo",
        data_inicio=inicio_2, data_fim=inicio_2 + timedelta(hours=1),
        status=StatusReserva.CONFIRMADA,
        reservado_para_categoria="professor", reservado_para_nome="Caio", reservado_para_telefone="62999992222",
    )

    url_retirar = reverse("chave-retirar", kwargs={"ambiente_id": ambiente.id})
    cliente_autenticado_vigilante.post(url_retirar, {"reserva": com_chave_nao_devolvida.id}, format="json")

    url_devolver = reverse("chave-devolver", kwargs={"ambiente_id": ambiente.id})
    cliente_autenticado_vigilante.post(url_devolver, {}, format="json")

    management.call_command("concluir_reservas_passadas")

    abertas_e_vencidas = Reserva.objects.filter(
        ambiente=ambiente,
        status__in=[StatusReserva.PENDENTE, StatusReserva.CONFIRMADA],
        data_fim__lte=timezone.now(),
    )
    assert not abertas_e_vencidas.exists()

    sem_chave.refresh_from_db()
    com_chave_nao_devolvida.refresh_from_db()
    assert sem_chave.status == StatusReserva.CONCLUIDA
    assert com_chave_nao_devolvida.status == StatusReserva.CONCLUIDA
