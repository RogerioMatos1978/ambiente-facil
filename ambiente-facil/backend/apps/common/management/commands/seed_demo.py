"""Comando de gerenciamento para popular o banco com dados de demonstração.

Uso: python manage.py seed_demo
"""

from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.environments.models import Ambiente, TipoAmbiente
from apps.reservations.models import Reserva

User = get_user_model()


class Command(BaseCommand):
    help = "Cria usuários, ambientes e reservas de exemplo para demonstração do Ambiente Fácil."

    def handle(self, *args, **options):
        admin, criado = User.objects.get_or_create(
            username="admin",
            defaults=dict(
                papel="admin",
                first_name="Administrador",
                last_name="Geral",
                telefone="5511999990000",
                is_staff=True,
                is_superuser=True,
            ),
        )
        if criado:
            admin.set_password("Admin@123")
            admin.save()
            self.stdout.write(self.style.SUCCESS("Usuário admin/Admin@123 criado."))

        usuario, criado = User.objects.get_or_create(
            username="professor",
            defaults=dict(
                papel="user",
                first_name="Ana",
                last_name="Professora",
                telefone="5511988880000",
            ),
        )
        if criado:
            usuario.set_password("Usuario@123")
            usuario.save()
            self.stdout.write(self.style.SUCCESS("Usuário professor/Usuario@123 criado."))

        vigilante, criado = User.objects.get_or_create(
            username="vigilante",
            defaults=dict(
                papel="vigilante",
                first_name="Zé",
                last_name="da Guarita",
                telefone="5511955550000",
            ),
        )
        if criado:
            vigilante.set_password("Vigilante@123")
            vigilante.save()
            self.stdout.write(self.style.SUCCESS("Usuário vigilante/Vigilante@123 criado."))

        ambientes_dados = [
            ("Sala 101", TipoAmbiente.SALA_AULA, "Bloco A - 1º andar", 40, ["Projetor", "Quadro branco"]),
            ("Auditório Central", TipoAmbiente.AUDITORIO, "Bloco B - Térreo", 200, ["Som", "Projetor", "Palco"]),
            (
                "Laboratório de Informática 1",
                TipoAmbiente.LABORATORIO,
                "Bloco C - 2º andar",
                30,
                ["Computadores", "Projetor"],
            ),
            (
                "Sala de Reunião Diretoria",
                TipoAmbiente.SALA_REUNIAO,
                "Bloco A - 3º andar",
                12,
                ["TV", "Videoconferência"],
            ),
        ]
        ambientes = []
        for nome, tipo, local, capacidade, recursos in ambientes_dados:
            amb, _ = Ambiente.objects.get_or_create(
                nome=nome, defaults=dict(tipo=tipo, localizacao=local, capacidade=capacidade, recursos=recursos)
            )
            ambientes.append(amb)

        # Horário fixo (9h) para as reservas de exemplo — evita que o comando quebre
        # dependendo da hora em que é rodado (reservas só podem ir de 07:00 às 22:00,
        # no mesmo dia — ver Reserva.clean()).
        agora = timezone.localtime().replace(hour=9, minute=0, second=0, microsecond=0)
        exemplos = [
            (
                ambientes[0], "Aula de Redes de Computadores", agora + timedelta(hours=2), 2,
                "professor", "Ana Professora", "5511988880000",
            ),
            (
                ambientes[1], "Palestra de Boas-Vindas", agora + timedelta(days=1, hours=1), 3,
                "cliente", "Convidados Especiais", "5511977770000",
            ),
            (
                ambientes[2], "Oficina de Python", agora + timedelta(days=2), 4,
                "instrutor", "Carlos Instrutor", "5511966660000",
            ),
        ]
        for ambiente, titulo, inicio, horas, categoria, nome_reservado, telefone_reservado in exemplos:
            Reserva.objects.get_or_create(
                ambiente=ambiente,
                titulo=titulo,
                data_inicio=inicio,
                defaults=dict(
                    solicitante=usuario,
                    data_fim=inicio + timedelta(hours=horas),
                    reservado_para_categoria=categoria,
                    reservado_para_nome=nome_reservado,
                    reservado_para_telefone=telefone_reservado,
                ),
            )

        self.stdout.write(self.style.SUCCESS("Dados de demonstração criados com sucesso."))
