"""Serviços de notificação: e-mail automático e geração de mensagem/link para WhatsApp."""

import logging
from urllib.parse import quote

from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags

logger = logging.getLogger("apps.notifications")


def enviar_email_reserva(reserva, evento: str):
    """
    Envia e-mail automático para o solicitante sobre o evento da reserva.
    evento: 'criada' | 'confirmada' | 'cancelada' | 'lembrete'
    """
    if not reserva.notificar_email or not reserva.solicitante.email:
        return False

    assuntos = {
        "criada": f"Reserva criada: {reserva.titulo}",
        "confirmada": f"Reserva confirmada: {reserva.titulo}",
        "cancelada": f"Reserva cancelada: {reserva.titulo}",
        "lembrete": f"Lembrete de reserva: {reserva.titulo}",
    }
    assunto = assuntos.get(evento, f"Atualização da reserva: {reserva.titulo}")

    contexto = {"reserva": reserva, "evento": evento}
    try:
        corpo_html = render_to_string("notifications/email_reserva.html", contexto)
    except Exception:
        # Fallback simples caso o template não esteja disponível.
        corpo_html = (
            f"<p>Olá {reserva.solicitante.get_full_name()},</p>"
            f"<p>Sua reserva <strong>{reserva.titulo}</strong> no ambiente "
            f"<strong>{reserva.ambiente.nome}</strong> foi {evento}.</p>"
            f"<p>Início: {reserva.data_inicio:%d/%m/%Y %H:%M}<br>Fim: {reserva.data_fim:%d/%m/%Y %H:%M}</p>"
        )
    corpo_texto = strip_tags(corpo_html)

    try:
        send_mail(
            subject=assunto,
            message=corpo_texto,
            html_message=corpo_html,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[reserva.solicitante.email],
            fail_silently=False,
        )
        return True
    except Exception:
        logger.exception("Falha ao enviar e-mail de notificação da reserva %s", reserva.id)
        return False


def montar_mensagem_whatsapp(reserva) -> str:
    """Monta o texto da mensagem de WhatsApp para confirmação/lembrete de uma reserva."""
    return (
        f"Olá {reserva.solicitante.get_full_name()}! Confirmando sua reserva no *Ambiente Fácil*:\n"
        f"Nº de controle: {reserva.numero_controle}\n"
        f"Ambiente: {reserva.ambiente.nome}\n"
        f"Título: {reserva.titulo}\n"
        f"Início: {reserva.data_inicio:%d/%m/%Y %H:%M}\n"
        f"Fim: {reserva.data_fim:%d/%m/%Y %H:%M}\n"
        f"Duração: {reserva.duracao_display}\n"
        f"Status: {reserva.get_status_display()}"
    )


def montar_link_whatsapp(reserva) -> dict:
    """
    Retorna telefone, mensagem e link prontos para uso no botão do frontend.

    Usa o esquema `whatsapp://send` (em vez de `https://wa.me/`) para abrir
    diretamente o aplicativo do WhatsApp instalado e logado no computador,
    sem passar pelo navegador/WhatsApp Web. Requer o WhatsApp Desktop
    instalado na máquina que aciona o botão.
    """
    telefone = reserva.solicitante.whatsapp_e164
    if telefone and not telefone.startswith(settings.WHATSAPP_DEFAULT_COUNTRY_CODE) and len(telefone) <= 11:
        telefone = f"{settings.WHATSAPP_DEFAULT_COUNTRY_CODE}{telefone}"
    mensagem = montar_mensagem_whatsapp(reserva)
    link = f"whatsapp://send?phone={telefone}&text={quote(mensagem)}" if telefone else None
    return {"telefone": telefone, "mensagem": mensagem, "link": link}
