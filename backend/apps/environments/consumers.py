"""Consumer WebSocket que transmite em tempo real o status (livre/ocupado) dos ambientes."""


from channels.generic.websocket import AsyncJsonWebsocketConsumer


class PainelAmbientesConsumer(AsyncJsonWebsocketConsumer):
    """
    Painel visual em tempo real.
    Cada cliente conectado entra no grupo 'painel_ambientes' e recebe eventos
    sempre que uma reserva é criada, cancelada ou seu status muda.
    """

    GROUP_NAME = "painel_ambientes"

    async def connect(self):
        if not self.scope["user"] or not self.scope["user"].is_authenticated:
            await self.close(code=4401)
            return
        await self.channel_layer.group_add(self.GROUP_NAME, self.channel_name)
        await self.accept()
        await self.send_json({"tipo": "conexao", "mensagem": "Conectado ao painel em tempo real."})

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.GROUP_NAME, self.channel_name)

    async def receive_json(self, content, **kwargs):
        # Canal é somente para broadcast do servidor; ignoramos mensagens do cliente.
        pass

    async def ambiente_atualizado(self, event):
        """Handler chamado quando o backend publica um evento no grupo (ver signals.py)."""
        await self.send_json(event["payload"])
