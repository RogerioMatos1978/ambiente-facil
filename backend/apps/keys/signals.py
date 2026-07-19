"""Provisiona a chave de um ambiente automaticamente assim que ele é criado, para que
`Reserva.chave_status` (ver apps.reservations.serializers) e a Guarita de Chaves sempre
encontrem uma Chave já existente — sem depender de alguém abrir a tela da guarita antes."""

from django.db.models.signals import post_save
from django.dispatch import receiver

from apps.environments.models import Ambiente

from .models import Chave


@receiver(post_save, sender=Ambiente)
def criar_chave_para_novo_ambiente(sender, instance, created, **kwargs):
    if created:
        Chave.objects.get_or_create(ambiente=instance)
