"""Horários fixos e seguros para os testes de reserva.

Desde que passou a existir a regra de negócio que restringe reservas a 07:00–22:00,
no mesmo dia (ver Reserva.clean()), testes que usavam `timezone.now() + timedelta(...)`
ficaram sujeitos a falhar dependendo da hora real em que a suíte roda (ex.: rodar às
20h e somar 6 horas ultrapassa as 22h e vira o dia). Estes helpers fixam um horário
seguro (bem no meio da janela permitida) para o futuro e para o passado.
"""

from datetime import timedelta

from django.utils import timezone


def horario_futuro():
    """Amanhã às 09:00 (horário local) — sempre dentro da janela permitida, com folga
    de até 13h para somar deslocamentos nos testes sem sair de 07:00–22:00."""
    return (timezone.localtime() + timedelta(days=1)).replace(hour=9, minute=0, second=0, microsecond=0)


def horario_passado():
    """Ontem às 10:00 (horário local) — sempre no passado (independente de quando a
    suíte roda) e dentro da janela permitida."""
    return (timezone.localtime() - timedelta(days=1)).replace(hour=10, minute=0, second=0, microsecond=0)
