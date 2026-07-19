"""Serviços de notificação: geração de mensagem/link para WhatsApp.

O sistema não envia e-mail (o campo de e-mail foi removido do usuário e a notificação
automática por e-mail ao criar/confirmar/cancelar reserva foi retirada). O WhatsApp,
acionado manualmente pelo botão na tela de detalhes da reserva, é o único canal de
notificação.
"""

from urllib.parse import quote

from django.conf import settings


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
