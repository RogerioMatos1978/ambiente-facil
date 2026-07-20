# Ambiente Fácil

Sistema web para gerenciamento e agendamento de ambientes institucionais (salas de aula,
auditórios, laboratórios e salas de reunião), com prevenção automática de conflitos de
horário, painel de disponibilidade em tempo real, notificação por WhatsApp, auditoria
completa e exportação de relatórios. O sistema não usa e-mail: o telefone (WhatsApp) é o
único contato do usuário e o único canal de notificação.

## Stack

- **Backend:** Python, Django, Django REST Framework, Django Channels (WebSocket), PostgreSQL, Redis.
- **Frontend:** Next.js (App Router) + TypeScript + TailwindCSS + shadcn/ui (Radix UI).
- **Autenticação:** JWT (access + refresh) com RBAC (Administrador / Usuário).
- **Infra:** Docker e Docker Compose (dev e produção), GitHub Actions (CI).

## Funcionalidades implementadas

- Autenticação JWT com dois perfis (Administrador e Usuário) e permissões RBAC em cada endpoint.
- Cadastro de ambientes (tipo, capacidade, localização, recursos, foto).
- Cadastro de usuários (admin) com telefone (WhatsApp, obrigatório — único contato do usuário; não há campo de e-mail no sistema) e departamento.
- Três perfis de usuário, escolhidos pelo admin ao cadastrar (`/usuarios`): **Administrador** (acesso total), **Usuário** (solicita reservas, vê a agenda) e **Guarita** (código interno "vigilante" — acesso restrito só à Guarita de Chaves; não enxerga dashboard, calendário, reservas, ambientes, usuários nem auditoria, nem pela tela nem pela API).
- Reservas com **prevenção automática de conflitos de horário** (validada no modelo e na API).
- A lista de reservas é uma **agenda compartilhada**: qualquer usuário autenticado vê todas as reservas de todos os ambientes (não só as próprias) — inclusive nas exportações e no relatório.
- O filtro de período (`data_de`/`data_ate`, usado no calendário, no relatório e nas exportações) considera reservas que **se sobrepõem** à janela pesquisada, não só as totalmente contidas nela — corrige um bug em que reservas que cruzavam o início/fim do período filtrado somem do calendário.
- Qualquer usuário pode solicitar (criar) uma reserva; **editar, excluir ou cancelar reservas já existentes é exclusivo de administradores**. Reservas cujo período já terminou são concluídas automaticamente e ficam somente leitura (ver seção "Check-in automático e reserva rápida").
- **Horário permitido: 07:00 às 22:00, no mesmo dia** — o sistema recusa reservas fora dessa janela ou que atravessem a meia-noite (validado no modelo e na API, ver `Reserva.clean()`).
- Toda reserva exige o campo **Reservado para**: categoria (Professor, Instrutor, Cliente, Limpeza ou Manutenção) + nome e telefone de quem vai efetivamente usar a sala — pode ser diferente de quem está logado fazendo a reserva. Aparece nos detalhes da reserva, nas exportações e na mensagem da guarita (abaixo).
- Cada reserva mostra, na tela de detalhes, uma **mensagem de instruções para a guarita**: retirar a chave ao chegar, verificar o ambiente, zelar pela conservação e devolver a chave no fim do uso — e essa mensagem é a que vai por WhatsApp para o responsável (ver os dois itens abaixo e "Guarita de Chaves" mais adiante).
- Cancelamento de reservas com motivo e histórico de quem cancelou.
- Painel de ambientes livres/ocupados **em tempo real via WebSocket** (Django Channels + Redis). Cada card ocupado mostra um texto objetivo ("Libera às HH:mm") e, ao passar o mouse, um balão com os detalhes completos da reserva em andamento (título, reservado para, solicitante, horário e duração).
- Calendário no frontend com visões **Dia / Semana / Mês / Agenda**, inspirado no Outlook e Google Calendar.
- Dashboard com indicadores (KPIs) e gráfico de reservas da semana.
- Botão "Enviar WhatsApp" (só aparece em reservas com **status Confirmada** — o backend também recusa a chamada para os demais status) que monta a mensagem (confirmação da reserva + instruções da guarita) e abre um link **`https://wa.me/...`** em nova aba — funciona com o WhatsApp Desktop instalado ou, na falta dele, com o WhatsApp Web pelo navegador. A mensagem vai para o telefone de **quem vai efetivamente usar a sala** ("Reservado para"), não para quem apenas fez a reserva no sistema — cai para o telefone do solicitante só se o do responsável não tiver sido informado (reservas antigas).
- A lista de **Reservas** mostra também o **status da chave** do ambiente (Disponível / Ocupada), refletindo em tempo real o que está acontecendo na Guarita de Chaves.
- A tela de **Reservas** vem ordenada pelo **Nº de controle, do maior para o menor** (mais recente primeiro) e filtrada por **status Confirmada** por padrão; tem campos de busca (título/descrição/ambiente), filtro por ambiente, status e período, e um botão para limpar os filtros — os mesmos filtros valem para as exportações CSV/Excel/PDF dessa tela.
- Auditoria completa: toda criação, atualização, cancelamento e exportação fica registrada
  (usuário, IP, data/hora), além do histórico de alterações de cada registro (django-simple-history).
- Exportação de reservas em **CSV, Excel (XLSX) e PDF**.
- Toda reserva recebe um **número de controle sequencial** (`RES-000123`, derivado do id) — aparece na mensagem de WhatsApp, na tela de detalhes e nas exportações CSV/Excel/PDF.
- Toda reserva mostra sua **duração** (ex.: `1h30min`) — na lista de reservas, na tela de detalhes, no calendário, na página de check-in, na mensagem de WhatsApp e nas exportações CSV/Excel/PDF.
- Página de **Relatórios** (`/relatorios`): KPIs (total, confirmadas, taxa de no-show, duração média), gráfico de reservas por dia, reservas por status, ranking de ambientes mais reservados e (para administradores) ranking de quem mais reservou — tudo filtrável por período/ambiente/status e exportável em CSV/Excel/PDF.
- Tema claro/escuro (persistido) em todo o frontend.
- Botão **"Atualizar site"** (ícone de recarregar) na barra superior de toda página do painel e na página de check-in/QR code — recarrega a página sem depender do usuário lembrar do atalho do navegador. A sessão não é derrubada por isso: o refresh token é renovado corretamente a cada uso (ver "Correções" abaixo).
- Página **Configurações** (`/configuracoes`, só administrador): reúne os controles de aparência (tema claro/escuro e cor institucional — continuam disponíveis também na barra superior, é preferência pessoal salva no navegador) e uma configuração nova, global: o **estilo dos ícones do menu** (padrão, contornado ou preenchido), que vale para todos os usuários do sistema e fica salvo no backend (`GET/PATCH /api/v1/configuracao-sistema/`).
- **Seletor de cores institucionais** (ícone de paleta na barra superior): 5 temas baseados no Manual de Marcas do Sistema FIEG (SESI/SENAI/IEL Goiás, ago/2024). O padrão "SESI SENAI" usa o azul institucional `#164194`; os temas SESI (`#52AE32` verde), SENAI (`#E84910` laranja), IEL (`#6CC2BA` verde-água) e Sistema FIEG (`#008BD2` azul claro) trocam a cor dominante do sistema inteiro (botões, menu ativo, badges, foco) para essa cor de detalhe da marca escolhida. Funciona em conjunto com o tema claro/escuro e a escolha fica salva no navegador.
- API documentada com OpenAPI/Swagger (`/api/docs`) e Redoc (`/api/redoc`).
- Testes automatizados (pytest) cobrindo conflito de horários, RBAC e autenticação.
- Rate limiting no login e em escritas de reservas, CORS/CSRF configurados, logs rotativos.
- CI (GitHub Actions): lint + testes do backend, type-check + lint + build do frontend, build das imagens Docker.
- **Check-in / liberação automática por no-show**: ambientes marcados com "exige check-in" liberam a
  reserva sozinhos se ninguém confirmar presença dentro da tolerância configurada (padrão 15 min),
  evitando salas reservadas e vazias. Roda em segundo plano automaticamente (APScheduler), sem precisar
  de cron externo; também pode ser disparado manualmente com `python manage.py liberar_no_show`.
- **Reserva rápida + QR code por sala**: cada ambiente tem um QR code (`/ambientes/qrcodes`, pronto
  para imprimir e colar na porta) que leva à página `/checkin/<id>` — mostra se a sala está
  livre/ocupada, permite reservar na hora (15/30/45/60/90/120 min) ou confirmar check-in pelo celular.
- **Cards de sala clicáveis**: no painel em tempo real e na tela de Ambientes, clicar num ambiente
  livre abre direto o formulário de nova reserva já com o ambiente selecionado.
- **Totalmente responsivo para celular**: menu lateral vira uma gaveta deslizante (ícone de menu no
  topo) abaixo do breakpoint `md`, tabelas fazem scroll horizontal e escondem colunas secundárias em
  telas pequenas, formulários empilham os campos em vez de ficar apertados, e o calendário (visão Mês)
  tem scroll horizontal seguro.

## Rodando localmente com Docker (recomendado)

```bash
cp .env.example .env
docker compose up --build
```

- Backend: http://localhost:8000 — Swagger em http://localhost:8000/api/docs
- Frontend: http://localhost:3000
- Após subir, rode as migrações e (opcionalmente) dados de exemplo:

```bash
docker compose exec backend python manage.py migrate
docker compose exec backend python manage.py seed_demo
```

O comando `seed_demo` cria dois usuários de teste:

| Usuário     | Senha          | Perfil         |
|-------------|----------------|----------------|
| admin       | Admin@123      | Administrador  |
| professor   | Usuario@123    | Usuário comum  |
| vigilante   | Vigilante@123  | Guarita (só Guarita de Chaves) |

## Produção em rede local (intranet, sem acesso externo)

Para rodar em um PC de uma rede interna, servindo os outros computadores da rede, sem domínio nem
certificado HTTPS:

```bash
cp .env.prod.example .env
# edite o .env: troque todo "<IP-DO-PC>" pelo IP fixo do PC que vai servir o sistema
docker compose -f docker-compose.prod.yml up -d --build
```

- Acesso: `http://<IP-DO-PC>` (porta 80, via Nginx) — mesmo endereço para todos os PCs da rede.
- Reserve um IP fixo para esse PC no roteador (DHCP reservation) ou configure IP estático no Windows;
  se o IP mudar depois, o frontend precisa ser rebuildado (o endereço da API é embutido no build do
  Next.js, não é lido em tempo de execução).
- `DJANGO_SECRET_KEY` do `.env.prod.example` é só um placeholder — gere uma chave de verdade com
  `python -c "import secrets; print(secrets.token_urlsafe(50))"` antes de usar em produção.
- O backend roda com Gunicorn + worker ASGI (`uvicorn.workers.UvicornWorker`), necessário para o
  WebSocket do painel em tempo real funcionar também em produção (não só a API REST).
- Se editar o `.env` depois que os containers já estão no ar (ex.: mudar `FRONTEND_URL`), `docker compose restart backend` **não é suficiente** — ele reinicia o mesmo container sem reler o `.env`. Use `docker compose -f docker-compose.prod.yml up -d --force-recreate backend` para recriar o container com as variáveis atualizadas. Para conferir o que o container está usando de fato: `docker compose -f docker-compose.prod.yml exec backend printenv FRONTEND_URL`.

## Rodando sem Docker

### Backend

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt
cp ../.env.example ../.env   # ajuste POSTGRES_HOST=localhost e REDIS_HOST=localhost
python manage.py migrate
python manage.py seed_demo
daphne -b 0.0.0.0 -p 8000 config.asgi:application
```

É necessário ter PostgreSQL e Redis rodando localmente (ou via `docker compose up db redis`).

### Frontend

```bash
cd frontend
npm install
cp .env.local.example .env.local
npm run dev
```

### Testes do backend

```bash
cd backend
DJANGO_SETTINGS_MODULE=config.settings.test pytest
```

## Estrutura do projeto

```
ambiente-facil/
├── backend/
│   ├── apps/
│   │   ├── accounts/        # usuários, papéis (RBAC), login JWT
│   │   ├── environments/    # ambientes + WebSocket (painel em tempo real)
│   │   ├── reservations/    # reservas + prevenção de conflitos
│   │   ├── audit/           # logs de auditoria
│   │   ├── notifications/   # mensagem/link do WhatsApp
│   │   ├── keys/            # Guarita de Chaves (admin + vigilante)
│   │   └── common/          # permissões, exportações, middleware, exceções
│   ├── config/               # settings (base/dev/test/prod), urls, asgi/wsgi
│   └── tests/
├── frontend/
│   └── src/
│       ├── app/              # rotas (App Router): login, dashboard, calendário...
│       ├── components/       # ui (shadcn), calendar, reservations, dashboard, layout
│       ├── hooks/, lib/, store/, types/
├── docker/                    # nginx.conf (produção)
├── .github/workflows/ci.yml
├── docker-compose.yml         # desenvolvimento
└── docker-compose.prod.yml    # produção (Nginx + Gunicorn + build otimizado)
```

## Check-in automático e reserva rápida

Dois recursos pensados para uso em rede local/intranet (sem depender de internet ou serviços externos):

**Check-in / no-show.** Em cada ambiente (`Editar ambiente` no frontend, ou `exige_checkin` na API/admin),
é possível marcar "Exige check-in" e definir a tolerância em minutos (padrão 15). Reservas nesses
ambientes ficam com status "aguardando check-in"; se ninguém confirmar presença
(`POST /api/v1/reservations/<id>/checkin/`) dentro da tolerância, a reserva é liberada sozinha
(status `expirada`) por um agendador em segundo plano (APScheduler, inicia junto com o processo do
backend — configurável via `NO_SHOW_SCHEDULER_ATIVO` e `NO_SHOW_INTERVALO_MINUTOS` no `.env`).
Também dá para rodar manualmente: `python manage.py liberar_no_show`.

**Conclusão automática e regras de alteração.** Um segundo job em segundo plano (mesmo
agendador/intervalo do item acima) roda `python manage.py concluir_reservas_passadas`
periodicamente: toda reserva pendente/confirmada cujo horário de término já passou vira
`concluída` automaticamente. A partir daí ela é somente leitura — não pode mais ser editada,
excluída ou cancelada, nem por administrador. Além disso, **editar, excluir ou cancelar uma
reserva já existente passou a ser privilégio exclusivo de administradores**; qualquer usuário
autenticado ainda pode solicitar (criar) uma reserva normalmente, mas só um admin pode alterá-la
ou liberar a sala cancelando-a — e só enquanto ela ainda estiver dentro do período vigente.

**Reserva rápida + QR code.** `POST /api/v1/reservations/rapida/` cria uma reserva começando agora,
por uma duração curta (15 a 120 min) — é o que a página `/checkin/<ambiente_id>` usa (destino do
QR code de cada sala). Cada ambiente expõe um QR code em
`GET /api/v1/environments/<id>/qrcode/` (público, sem autenticação — só contém um link) apontando
para essa página; a tela `/ambientes/qrcodes` reúne o QR code de todos os ambientes prontos para
impressão e para colar na porta de cada sala. Requer `FRONTEND_URL` configurado corretamente no
`.env` (endereço que os usuários realmente acessam pelo navegador) para os QR codes apontarem para
o lugar certo.

## Guarita de Chaves

Controle físico da chave de cada ambiente, pensado para a portaria/guarita de uma unidade
SESI/SENAI: uma chave por ambiente (provisionada automaticamente), sempre amarrada à reserva do
dia correspondente, não um controle solto.

- **Acesso**: administrador (vê e altera tudo) e o novo perfil **Vigilante** (retira e devolve
  chaves). Usuário comum não tem acesso — nem pela tela (`/guarita-chaves` não aparece no menu),
  nem pela API (`IsAdminOuVigilante`, ver `apps/keys/views.py`). O vigilante, por sua vez, só
  enxerga essa tela: todo o resto do sistema (dashboard, calendário, reservas, ambientes,
  relatórios) é bloqueado tanto na navegação quanto na API (`apps.common.permissions.NaoEhVigilante`).
- **Fluxo (só dois estados: disponível ↔ ocupada, sem etapa intermediária)**: a tela lista cada
  ambiente com as reservas do dia; retirar a chave exige escolher a reserva correspondente
  (`POST /api/v1/guarita/chaves/<ambiente_id>/retirar/`). **Devolver** (`.../devolver/`) faz tudo
  de uma vez, num único clique, para qualquer perfil (inclusive administrador): encerra a reserva
  vinculada (`Reserva.status = concluída`), libera a sala e deixa a chave disponível para o
  próximo uso. **Não existe ação "repor"** — foi removida por completo (não há mais um estado
  "devolvida" nem uma etapa de conferência manual depois de devolver, para ninguém). Toda ação
  fica registrada na auditoria.
- **Nenhuma reserva fica em aberto**: isso é garantido em duas frentes independentes, que juntas
  cobrem qualquer cenário. (1) Ao devolver a chave na guarita, a reserva vinculada é concluída na
  hora (acima). (2) Mesmo que a chave nunca seja devolvida, um job em segundo plano
  (`concluir_reservas_passadas`, mesmo agendador do check-in automático, ver
  `apps/reservations/apps.py`) roda a cada poucos minutos e conclui automaticamente qualquer
  reserva "pendente"/"confirmada" cujo horário já tenha passado — com ou sem chave envolvida. Ou
  seja: mesmo se a chave física nunca voltar pra guarita, a agenda nunca fica presa indefinidamente
  (só a chave em si continua "ocupada" até alguém devolvê-la de fato).
- **Mensagem da guarita**: a tela de detalhes de qualquer reserva mostra as instruções para quem
  vai usar a sala — retirar a chave na guarita ao chegar, verificar o ambiente, zelar pela
  conservação e devolver a chave ao final (`Reserva.mensagem_guarita`).
- **Notificação em tempo real é "melhor esforço"**: se o Redis (usado pelo WebSocket do painel em
  tempo real) estiver indisponível, isso nunca impede a reserva de ser encerrada nem a chave de
  ser liberada ao devolver — só o aviso instantâneo na tela é que não chega, e volta a funcionar
  assim que o Redis voltar (ver `apps/environments/signals.py`). As ações da guarita
  (`retirar`/`devolver`) também rodam em transação: reserva e chave são salvas juntas, sem risco
  de ficar uma atualizada e a outra não.

## Arquitetura e decisões

O backend segue uma separação por apps de domínio (accounts, environments, reservations,
audit, notifications) desacoplados entre si — por exemplo, `reservations` não conhece diretamente `notifications`, ele só monta a mensagem/link do WhatsApp sob demanda quando o botão é clicado no frontend. Não há notificação automática disparada por signals: o sistema não usa e-mail e o WhatsApp é sempre uma ação manual do usuário. Isso mantém os apps coesos e facilita testes e evolução (Clean Architecture / SOLID aplicados de forma pragmática ao Django).

A prevenção de conflitos de horário é garantida em duas camadas: no método `Reserva.clean()`
(regra de negócio, testável isoladamente) e refletida na resposta da API (mensagem de erro clara
para o usuário).

A autenticação do WebSocket usa um middleware próprio (`apps/common/ws_auth.py`) que valida o
mesmo token JWT usado na API REST — o cliente conecta em `wss://.../ws/painel-ambientes/?token=<access>`.

## Roadmap de integrações futuras

O sistema foi desenhado para receber, sem redesenho estrutural:

- **Microsoft 365 / Outlook Calendar** e **Google Calendar**: sincronização de reservas via
  Microsoft Graph API / Google Calendar API. O modelo `Reserva` e o app `notifications` já
  isolam a lógica de envio, bastando adicionar um novo serviço de sincronização.
- **LDAP / Active Directory**: o modelo `User` já possui os campos `identificador_externo` e
  `provedor_externo` para mapear contas externas; bastaria adicionar `django-auth-ldap` e um
  backend de autenticação adicional.
- **Outros sistemas institucionais**: a API REST documentada (OpenAPI/Swagger) permite integração
  direta por outros sistemas.

## Segurança

- Autenticação via JWT (access curto + refresh com rotação e blacklist).
- RBAC em todos os endpoints sensíveis (permissões `IsAdmin`, `IsAdminOrReadOnly`, `IsOwnerOrAdmin`).
- CORS e CSRF configurados por variável de ambiente.
- Rate limiting (throttling) no login e em escritas de reservas.
- Logs estruturados (console + arquivo rotativo) e auditoria de ações sensíveis.
- Configurações de produção (`config/settings/prod.py`) com HSTS, cookies seguros e SSL redirect.
- Backup: recomenda-se `pg_dump` agendado (ex.: cron ou job do orquestrador) apontando para o
  serviço `db` do Docker Compose; o volume `postgres_data` mantém os dados entre reinícios.
