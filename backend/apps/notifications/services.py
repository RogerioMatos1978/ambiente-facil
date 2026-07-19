"""Serviços de notificação: geração de mensagem/link para WhatsApp.

O sistema não envia e-mail (o campo de e-mail foi removido do usuário e a notificação
automática por e-mail ao criar/confirmar/cancelar reserva foi retirada). O WhatsApp,
acionado manualmente pelo botão na tela de detalhes da reserva, é o único canal de
notificação — e vai para quem vai efetivamente usar a sala (campo "Reservado para"),
não para quem apenas fez a reserva no sistema (a menos que sejam a mesma pessoa, ou
que o telefone do responsável não tenha sido informado).
"""

from urllib.parse import quote

from django.conf import settings


def _telefone_e164(telefone_bruto: str) -> str:
    """Limpa um telefone (só dígitos) e garante o DDI, igual a User.whatsapp_e164 —
    mas aceita qualquer string, não só o telefone de um usuário cadastrado."""
    digitos = "".join(ch for ch in (telefone_bruto or "") if ch.isdigit())
    if digitos and not digitos.startswith(settings.WHATSAPP_DEFAULT_COUNTRY_CODE) and len(digitos) <= 11:
        digitos = f"{settings.WHATSAPP_DEFAULT_COUNTRY_CODE}{digitos}"
    return digitos


def montar_mensagem_whatsapp(reserva) -> str:
    """
    Monta o texto da mensagem de WhatsApp: confirmação da reserva + as instruções da
    guarita (retirar a chave, verificar o ambiente, zelar, devolver) — mesmo texto que
    aparece na tela de detalhes (ver Reserva.mensagem_guarita).
    """
    nome_responsavel = reserva.reservado_para_nome or reserva.solicitante.get_full_name()
    partes = [
        f"Olá {nome_responsavel}! Confirmando sua reserva no *Ambiente Fácil*:",
        f"Nº de controle: {reserva.numero_controle}",
        f"Ambiente: {reserva.ambiente.nome}",
        f"Título: {reserva.titulo}",
        f"Início: {reserva.data_inicio:%d/%m/%Y %H:%M}",
        f"Fim: {reserva.data_fim:%d/%m/%Y %H:%M}",
        f"Duração: {reserva.duracao_display}",
        f"Status: {reserva.get_status_display()}",
        "",
        reserva.mensagem_guarita,
    ]
    return "\n".join(parte for parte in partes if parte)


def montar_link_whatsapp(reserva) -> dict:
    """
    Retorna telefone, mensagem e link prontos para uso no botão do frontend.

    O telefone é o de quem vai efetivamente usar a sala (`reservado_para_telefone`);
    se não tiver sido informado (reservas antigas, anteriores a este campo), cai para
    o telefone de quem solicitou a reserva.

    Usa `https://wa.me/` (em vez de `whatsapp://send`): nem todo mundo tem o WhatsApp
    Desktop instalado, e wa.me funciona tanto abrindo o app (se instalado) quanto o
    WhatsApp Web no navegador, como alternativa.
    """
    # _telefone_e164 cuida da limpeza e do prefixo de DDI nos dois casos — usar
    # solicitante.whatsapp_e164 aqui (que só limpa, sem prefixar) deixaria o fallback
    # inconsistente com o caminho principal.
    telefone = _telefone_e164(reserva.reservado_para_telefone) or _telefone_e164(reserva.solicitante.telefone)
    mensagem = montar_mensagem_whatsapp(reserva)
    link = f"https://wa.me/{telefone}?text={quote(mensagem)}" if telefone else None
    return {"telefone": telefone, "mensagem": mensagem, "link": link}
