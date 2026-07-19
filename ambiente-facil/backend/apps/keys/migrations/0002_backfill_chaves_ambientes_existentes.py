# Cria a Chave de todo Ambiente que já existia antes deste app (novos ambientes já
# ganham uma automaticamente via signal — ver apps/keys/signals.py).

from django.db import migrations


def criar_chaves_faltantes(apps, schema_editor):
    Ambiente = apps.get_model("environments", "Ambiente")
    Chave = apps.get_model("keys", "Chave")
    for ambiente in Ambiente.objects.filter(chave__isnull=True):
        Chave.objects.create(ambiente=ambiente)


def remover_chaves(apps, schema_editor):
    # Não desfaz de propósito: apagar chaves na reversão perderia o histórico de
    # retirada/devolução em andamento sem necessidade.
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("keys", "0001_initial"),
        ("environments", "0002_ambiente_exige_checkin_and_more"),
    ]

    operations = [
        migrations.RunPython(criar_chaves_faltantes, remover_chaves),
    ]
