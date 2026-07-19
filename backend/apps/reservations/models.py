"""Modelo de Reserva com prevenção de conflitos de horário e controle de check-in/no-show."""

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone
from simple_history.models import HistoricalRecords


class StatusReserva(models.TextChoices):
    PENDENTE = "pendente", "Pendente"
    CONFIRMADA = "confirmada", "Confirmada"
    CANCELADA = "cancelada", "Cancelada"
    CONCLUIDA = "concluida", "Concluída"
    EXPIRADA = "expirada", "Expirada (no-show)"


class Reserva(models.Model):
    ambiente = models.ForeignKey("environments.Ambiente", on_delete=models.PROTECT, related_name="reservas")
    solicitante = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="reservas")
    titulo = models.CharField(max_length=200)
    descricao = models.TextField(blank=True)
    data_inicio = models.DateTimeField()
    data_fim = models.DateTimeField()
    status = models.CharField(max_length=12, choices=StatusReserva.choices, default=StatusReserva.CONFIRMADA)
    motivo_cancelamento = models.CharField(max_length=255, blank=True)
    cancelado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="reservas_canceladas",
    )
    cancelado_em = models.DateTimeField(null=True, blank=True)
    notificar_email = models.BooleanField(default=True)

    checkin_confirmado_em = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Check-in confirmado em",
        help_text="Preenchido quando o solicitante confirma presença. Usado para liberar a sala "
        "automaticamente em caso de no-show em ambientes que exigem check-in.",
    )

    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    history = HistoricalRecords()

    class Meta:
        verbose_name = "Reserva"
        verbose_name_plural = "Reservas"
        ordering = ["-data_inicio"]
        indexes = [
            models.Index(fields=["ambiente", "data_inicio", "data_fim"]),
            models.Index(fields=["status"]),
        ]

    def __str__(self):
        return f"{self.titulo} - {self.ambiente} ({self.data_inicio:%d/%m/%Y %H:%M})"

    def clean(self):
        if self.data_inicio and self.data_fim and self.data_fim <= self.data_inicio:
            raise ValidationError("A data/hora de término deve ser posterior à de início.")
        if self.status in (StatusReserva.PENDENTE, StatusReserva.CONFIRMADA):
            conflitos = self.conflitos_existentes()
            if conflitos.exists():
                conflito = conflitos.first()
                raise ValidationError(
                    f"Conflito de horário: o ambiente '{self.ambiente}' já está reservado "
                    f"de {conflito.data_inicio:%d/%m/%Y %H:%M} até {conflito.data_fim:%d/%m/%Y %H:%M} "
                    f"(reserva '{conflito.titulo}')."
                )

    def conflitos_existentes(self):
        """Retorna reservas ativas do mesmo ambiente cujo intervalo se sobrepõe ao desta reserva."""
        qs = Reserva.objects.filter(
            ambiente=self.ambiente,
            status__in=[StatusReserva.PENDENTE, StatusReserva.CONFIRMADA],
            data_inicio__lt=self.data_fim,
            data_fim__gt=self.data_inicio,
        )
        if self.pk:
            qs = qs.exclude(pk=self.pk)
        return qs

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    @property
    def precisa_checkin(self) -> bool:
        """True se este ambiente exige check-in e a reserva ainda está aguardando confirmação."""
        return (
            self.status == StatusReserva.CONFIRMADA
            and getattr(self.ambiente, "exige_checkin", False)
            and self.checkin_confirmado_em is None
        )

    @property
    def prazo_checkin(self):
        """Horário-limite para confirmar check-in antes da liberação automática por no-show."""
        from datetime import timedelta

        minutos = getattr(self.ambiente, "tolerancia_checkin_minutos", 15)
        return self.data_inicio + timedelta(minutes=minutos)

    def checkin_expirado(self, agora=None) -> bool:
        """True se o prazo de check-in já passou e ninguém confirmou presença."""
        if not self.precisa_checkin:
            return False
        agora = agora or timezone.now()
        return agora >= self.prazo_checkin
