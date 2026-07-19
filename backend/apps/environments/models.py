"""Modelos de Ambientes institucionais (salas de aula, auditórios, laboratórios, salas de reunião)."""

from django.db import models
from simple_history.models import HistoricalRecords


class TipoAmbiente(models.TextChoices):
    SALA_AULA = "sala_aula", "Sala de Aula"
    AUDITORIO = "auditorio", "Auditório"
    LABORATORIO = "laboratorio", "Laboratório"
    SALA_REUNIAO = "sala_reuniao", "Sala de Reunião"
    OUTRO = "outro", "Outro"


class Ambiente(models.Model):
    nome = models.CharField(max_length=150)
    tipo = models.CharField(max_length=20, choices=TipoAmbiente.choices, default=TipoAmbiente.SALA_AULA)
    localizacao = models.CharField(max_length=200, blank=True, help_text="Bloco, andar, ala etc.")
    capacidade = models.PositiveIntegerField(default=0)
    recursos = models.JSONField(
        default=list,
        blank=True,
        help_text="Lista de recursos disponíveis, ex.: ['Projetor', 'Ar-condicionado', 'Quadro branco']",
    )
    descricao = models.TextField(blank=True)
    foto = models.ImageField(upload_to="ambientes/", blank=True, null=True)
    ativo = models.BooleanField(default=True)

    exige_checkin = models.BooleanField(
        default=False,
        verbose_name="Exige check-in",
        help_text="Se marcado, reservas deste ambiente são liberadas automaticamente por no-show "
        "quando ninguém confirma o check-in dentro da tolerância.",
    )
    tolerancia_checkin_minutos = models.PositiveIntegerField(
        default=15,
        verbose_name="Tolerância de check-in (minutos)",
        help_text="Minutos após o início da reserva antes de liberar o ambiente automaticamente por no-show.",
    )

    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    history = HistoricalRecords()

    class Meta:
        verbose_name = "Ambiente"
        verbose_name_plural = "Ambientes"
        ordering = ["nome"]

    def __str__(self):
        return f"{self.nome} ({self.get_tipo_display()})"
