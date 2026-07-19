from django.utils import timezone
from rest_framework import mixins, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError as DRFValidationError
from rest_framework.permissions import BasePermission
from rest_framework.response import Response

from apps.audit.models import AcaoAuditoria, registrar
from apps.common.permissions import IsAdmin
from apps.environments.models import Ambiente
from apps.reservations.models import Reserva, StatusReserva

from .models import Chave, StatusChave
from .serializers import ChaveSerializer


class IsAdminOuVigilante(BasePermission):
    """Acesso à Guarita de Chaves: administrador (tudo) ou vigilante (retirar/devolver/
    repor). Usuário comum não tem acesso nenhum a esta API."""

    message = "Apenas administradores ou vigilantes têm acesso à Guarita de Chaves."

    def has_permission(self, request, view):
        user = request.user
        return bool(user and user.is_authenticated and (user.is_admin or user.is_vigilante))


class ChaveViewSet(
    mixins.RetrieveModelMixin,
    mixins.ListModelMixin,
    mixins.UpdateModelMixin,
    viewsets.GenericViewSet,
):
    """
    Painel da Guarita de Chaves — uma chave por ambiente, provisionada automaticamente.
    Listagem/consulta e as ações retirar/devolver/repor: administrador ou vigilante.
    Edição direta (PATCH/PUT, ex.: corrigir status manualmente): só administrador.

    Ciclo normal: disponível --(retirar, vinculando a uma reserva do dia)--> ocupada
    --(devolver)--> disponível de novo, já com a reserva encerrada e a sala liberada
    (tudo em uma ação só). "repor" continua existindo só como ajuste manual de admin
    para o caso raro de uma chave ficar parada em "devolvida" (ex.: PATCH direto).
    """

    serializer_class = ChaveSerializer
    lookup_field = "ambiente_id"
    lookup_url_kwarg = "ambiente_id"

    def get_queryset(self):
        sem_chave = Ambiente.objects.filter(ativo=True).exclude(chave__isnull=False)
        for ambiente in sem_chave:
            Chave.objects.get_or_create(ambiente=ambiente)
        return (
            Chave.objects.select_related("ambiente", "reserva_atual", "reserva_atual__solicitante", "retirada_por")
            .filter(ambiente__ativo=True)
        )

    def get_permissions(self):
        if self.action in {"update", "partial_update"}:
            return [IsAdmin()]
        return [IsAdminOuVigilante()]

    @action(detail=True, methods=["post"])
    def retirar(self, request, ambiente_id=None):
        """Marca a chave como retirada, vinculando-a à reserva do dia informada."""
        chave = self.get_object()
        reserva_id = request.data.get("reserva")
        if not reserva_id:
            raise DRFValidationError({"reserva": "Informe a reserva correspondente à retirada da chave."})
        try:
            reserva = Reserva.objects.get(pk=reserva_id, ambiente_id=chave.ambiente_id)
        except Reserva.DoesNotExist as exc:
            raise DRFValidationError({"reserva": "Reserva não encontrada para este ambiente."}) from exc
        if reserva.status not in (StatusReserva.PENDENTE, StatusReserva.CONFIRMADA):
            raise DRFValidationError({"detalhes": "Esta reserva não está mais ativa."})
        if chave.status != StatusChave.DISPONIVEL:
            raise DRFValidationError({"detalhes": "Esta chave já está retirada ou aguardando ser reposta."})

        chave.status = StatusChave.OCUPADA
        chave.reserva_atual = reserva
        chave.retirada_em = timezone.now()
        chave.retirada_por = request.user
        chave.devolvida_em = None
        chave.atraso_notificado_em = None
        chave.save()

        registrar(
            request.user,
            AcaoAuditoria.ATUALIZACAO,
            "Chave",
            chave.id,
            descricao=f"Chave de '{chave.ambiente.nome}' retirada na guarita para a reserva {reserva.numero_controle}.",
            request=request,
        )
        return Response(ChaveSerializer(chave).data)

    @action(detail=True, methods=["post"])
    def devolver(self, request, ambiente_id=None):
        """
        Marca a chave como devolvida à guarita — e nesse mesmo passo encerra a reserva
        correspondente (mesmo que o horário programado ainda não tivesse terminado) e
        libera tanto a sala quanto a chave para o próximo uso. Não existe mais um passo
        manual separado de "repor": devolver já deixa tudo disponível de novo.
        """
        chave = self.get_object()
        if chave.status != StatusChave.OCUPADA:
            raise DRFValidationError({"detalhes": "Esta chave não está retirada no momento."})

        agora = timezone.now()
        reserva = chave.reserva_atual

        if reserva and reserva.status in (StatusReserva.PENDENTE, StatusReserva.CONFIRMADA):
            reserva.status = StatusReserva.CONCLUIDA
            reserva.save()
            registrar(
                request.user,
                AcaoAuditoria.ATUALIZACAO,
                "Reserva",
                reserva.id,
                descricao=f"Reserva '{reserva.titulo}' encerrada ao devolver a chave na guarita.",
                request=request,
            )

        chave.status = StatusChave.DISPONIVEL
        chave.devolvida_em = agora
        chave.reserva_atual = None
        chave.retirada_em = None
        chave.retirada_por = None
        chave.atraso_notificado_em = None
        chave.save()

        registrar(
            request.user,
            AcaoAuditoria.ATUALIZACAO,
            "Chave",
            chave.id,
            descricao=f"Chave de '{chave.ambiente.nome}' devolvida na guarita — sala e chave disponíveis novamente.",
            request=request,
        )
        return Response(ChaveSerializer(chave).data)

    @action(detail=True, methods=["post"])
    def repor(self, request, ambiente_id=None):
        """Confere e pendura a chave de volta, deixando-a disponível para a próxima reserva."""
        chave = self.get_object()
        if chave.status != StatusChave.DEVOLVIDA:
            raise DRFValidationError({"detalhes": "Só é possível repor uma chave que já foi devolvida."})

        chave.status = StatusChave.DISPONIVEL
        chave.reserva_atual = None
        chave.retirada_em = None
        chave.retirada_por = None
        chave.devolvida_em = None
        chave.atraso_notificado_em = None
        chave.save()

        registrar(
            request.user,
            AcaoAuditoria.ATUALIZACAO,
            "Chave",
            chave.id,
            descricao=f"Chave de '{chave.ambiente.nome}' reposta e disponível novamente.",
            request=request,
        )
        return Response(ChaveSerializer(chave).data)
