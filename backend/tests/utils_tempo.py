"""Horários fixos e seguros para os testes de reserva.

Desde que passou a existir a regra de negócio que restringe reservas a 07:00–22:00,
no mesmo dia (ver Reserva.clean()), testes que usavam `timezone.now() + timedelta(...)`
ficaram sujeitos a falhar dependendo da hora real em que a suíte roda (ex.: rodar às
20h e somar 6 horas ultrapassa as 22h e vira o dia). Estes helpers fixam um horário
seguro (bem no meio da janela permitida) para o futuro e para o passado.
"""

from contextlib import contextmanager
from datetime import timedelta
from unittest.mock import patch

from django.utils import timezone


@contextmanager
def agora_fixo_no_horario_permitido():
    """
    Congela `timezone.now()` num horário fixo e seguro (hoje às 10:00, dentro da janela
    07:00-22:00) — para testes que precisam de deltas relativos a "agora" (ex.: tolerância
    de check-in/no-show em minutos, onde tanto o teste quanto o código sob teste precisam
    concordar sobre o que é "agora") sem depender da hora real em que a suíte roda. Sem
    isso, testes como "reserva começou há 5 minutos" viravam flakiness perto das 21h-22h
    (a janela permitida termina às 22:00, então somar a duração da reserva ultrapassava o
    limite dependendo do horário real de execução).

    Uso:
        with agora_fixo_no_horario_permitido() as agora:
            inicio = agora - timedelta(minutes=5)
            ...
    """
    momento = timezone.localtime().replace(hour=10, minute=0, second=0, microsecond=0)
    with patch("django.utils.timezone.now", return_value=momento):
        yield momento


def horario_futuro():
    """Amanhã às 09:00 (horário local) — sempre dentro da janela permitida, com folga
    de até 13h para somar deslocamentos nos testes sem sair de 07:00–22:00."""
    return (timezone.localtime() + timedelta(days=1)).replace(hour=9, minute=0, second=0, microsecond=0)


def horario_passado():
    """Ontem às 10:00 (horário local) — sempre no passado (independente de quando a
    suíte roda) e dentro da janela permitida."""
    return (timezone.localtime() - timedelta(days=1)).replace(hour=10, minute=0, second=0, microsecond=0)
