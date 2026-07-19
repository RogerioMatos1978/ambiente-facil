# Ambiente Fácil vs. Calenda (Smartrooms) — comparativo e propostas de melhoria

> **Nota (19/07/2026):** este documento foi o comparativo inicial. Várias das lacunas
> apontadas abaixo já foram implementadas desde então — marcadas com ✅. A seção "O que o
> Ambiente Fácil já tem" foi atualizada para refletir o estado atual.

Fonte analisada: https://calenda.com.br/smartrooms (produto corporativo de reserva de salas, pago por sala gerenciada).

## O que o Calenda oferece que o Ambiente Fácil ainda não tem

1. **Mapa interativo do escritório** — reserva de sala clicando na planta baixa, não só em lista/calendário. *(pendente)*
2. **Fluxo de aprovação** — certas salas/horários/usuários exigem confirmação de um administrador antes da reserva valer. *(pendente)*
3. **Permissões por sala/grupo** — não é só admin vs. usuário: dá pra restringir "só o time X pode reservar o Auditório". *(pendente)*
4. ✅ **Check-in / check-out e liberação automática por no-show** — implementado: ambientes com "exige check-in" liberam a reserva sozinhos se ninguém confirmar presença dentro da tolerância configurada.
5. ✅ **QR code na porta da sala** — implementado (`/ambientes/qrcodes`, um QR por ambiente levando à página `/checkin/<id>`, que mostra livre/ocupado e permite reservar ou fazer check-in pelo celular). O modo "tablet fixo na porta com auto-refresh" propriamente dito não foi feito — a página existe, mas pensada para o celular do usuário, não para rodar sozinha num tablet montado na parede.
6. ✅ **Relatórios avançados** — implementado (`/relatorios`: KPIs, taxa de no-show, duração média, reservas por dia/status, ranking de ambientes e de solicitantes, exportável). "Smart Insights" com sugestão automática de quando aumentar/reduzir salas não foi feito.
7. **Integrações SSO e calendário (Google/Microsoft)** — login único e sincronização bidirecional de agenda, geração automática de link do Meet/Teams. *(pendente — ver "Roadmap de integrações futuras" no README, já preparado estruturalmente)*
8. **Centro de custo** — custo por reserva (hora ou fixo), rastreável por usuário/departamento. *(pendente)*
9. ✅ **Reserva "instantânea" em poucos cliques** — implementado (`POST /reservations/rapida/`, atalho de 15/30/45/60/90/120 min a partir da página de check-in/QR code, e clicar num card de sala livre já abre o formulário com o ambiente preenchido).

## O que o Ambiente Fácil já tem (não precisa refazer)

Autenticação JWT + RBAC, CRUD de ambientes e usuários (telefone/WhatsApp como único contato — **não há mais campo de e-mail no sistema**), prevenção automática de conflito de horário, cancelamento com histórico, painel em tempo real (WebSocket), calendário Dia/Semana/Mês/Agenda com agenda compartilhada (todo usuário vê todas as reservas; só admin edita/cancela), dashboard com KPIs e gráfico semanal, página de Relatórios completa, número de controle sequencial e duração em cada reserva, check-in/no-show automático, reserva rápida + QR code por sala, botão "Enviar WhatsApp" que abre o WhatsApp Desktop (não mais e-mail nem WhatsApp Web), seletor de 5 temas de cor institucionais (SESI/SENAI/IEL Goiás), auditoria completa com histórico de alterações, exportação CSV/Excel/PDF, tema claro/escuro, layout responsivo para celular, documentação OpenAPI/Swagger, testes automatizados (33 testes).

## Prioridades sugeridas para rodar em ambiente LOCAL (sem depender de internet)

O ambiente é uma intranet fechada — isso muda a prioridade em relação ao Calenda, que é SaaS. Itens que dependem de OAuth/nuvem (SSO Google/Microsoft, geração de link do Meet/Teams) fazem pouco sentido aqui e ficam de fora ou como opcional. Os que funcionam 100% offline sobem de prioridade:

| # | Melhoria | Por quê funciona bem local | Esforço |
|---|---|---|---|
| 1 | **Check-in / no-show com liberação automática** | Resolve o problema mais citado (sala reservada e vazia) sem precisar de nada externo — só um job/checagem periódica no backend | Médio |
| 2 | **Fluxo de aprovação por sala** | Já existe RBAC e modelo de Reserva; é estender o status com "pendente" e notificar o admin | Médio |
| 3 | **Modo Kiosk/Tablet por sala** | Uma rota `/kiosk/<ambiente_id>` sem necessidade de login (ou com token fixo do dispositivo), tela somente-leitura com auto-refresh via o WebSocket que já existe | Médio |
| 4 | **QR code por sala** | Gerar e imprimir um QR code (biblioteca Python `qrcode`, sem depender de serviço externo) apontando para a rota de check-in/reserva daquela sala | Baixo |
| 5 | **Reserva rápida ("reservar agora")** | Atalho no dashboard: 1 clique reserva a sala livre mais próxima por 30/60 min | Baixo |
| 6 | **Permissões por sala/grupo** | Estende o RBAC atual com uma tabela de permissões `grupo ↔ ambiente` | Médio |
| 7 | **Relatórios de ocupação avançados** | Já existe base de auditoria/reservas; adicionar taxa de ocupação por sala, horários de pico (heatmap) | Médio |
| 8 | **Mapa interativo do escritório** | Maior esforço — precisa de um editor de planta baixa (upload de imagem + posicionar salas) | Alto |
| 9 | **Exportação ICS por sala (somente leitura)** | Permite assinar a agenda de uma sala no Outlook/Google local, sem OAuth — só um feed `.ics` público por token | Baixo |
| — | SSO Google/Microsoft, link automático Meet/Teams, centro de custo | Baixa prioridade / não recomendado para rede fechada sem internet | — |

## Próximo passo

Este documento é só o comparativo — nenhum código foi alterado ainda. Preciso saber por onde você quer começar antes de implementar, porque são features de porte bem diferente (de "baixo esforço" a "mudança estrutural").
