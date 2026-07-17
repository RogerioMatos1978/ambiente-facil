# Ambiente Fácil

Sistema web para gerenciamento e agendamento de ambientes institucionais (salas de aula,
auditórios, laboratórios e salas de reunião), com prevenção automática de conflitos de
horário, painel de disponibilidade em tempo real, notificações por e-mail/WhatsApp,
auditoria completa e exportação de relatórios.

## Stack

- **Backend:** Python, Django, Django REST Framework, Django Channels (WebSocket), PostgreSQL, Redis.
- **Frontend:** Next.js (App Router) + TypeScript + TailwindCSS + shadcn/ui (Radix UI).
- **Autenticação:** JWT (access + refresh) com RBAC (Administrador / Usuário).
- **Infra:** Docker e Docker Compose (dev e produção), GitHub Actions (CI).

## Funcionalidades implementadas

- Autenticação JWT com dois perfis (Administrador e Usuário) e permissões RBAC em cada endpoint.
- Cadastro de ambientes (tipo, capacidade, localização, recursos, foto).
- Cadastro de usuários (admin) com telefone para WhatsApp e departamento.
- Reservas com **prevenção automática de conflitos de horário** (validada no modelo e na API).
- Cancelamento de reservas com motivo e histórico de quem cancelou.
- Painel de ambientes livres/ocupados **em tempo real via WebSocket** (Django Channels + Redis).
- Calendário no frontend com visões **Dia / Semana / Mês / Agenda**, inspirado no Outlook e Google Calendar.
- Dashboard com indicadores (KPIs) e gráfico de reservas da semana.
- Notificação automática por e-mail ao criar/confirmar/cancelar uma reserva.
- Botão "Enviar WhatsApp" que monta a mensagem e abre `wa.me` com o texto preenchido.
- Auditoria completa: toda criação, atualização, cancelamento e exportação fica registrada
  (usuário, IP, data/hora), além do histórico de alterações de cada registro (django-simple-history).
- Exportação de reservas em **CSV, Excel (XLSX) e PDF**.
- Tema claro/escuro (persistido) em todo o frontend.
- API documentada com OpenAPI/Swagger (`/api/docs`) e Redoc (`/api/redoc`).
- Testes automatizados (pytest) cobrindo conflito de horários, RBAC e autenticação.
- Rate limiting no login e em escritas de reservas, CORS/CSRF configurados, logs rotativos.
- CI (GitHub Actions): lint + testes do backend, type-check + lint + build do frontend, build das imagens Docker.

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

| Usuário     | Senha        | Perfil         |
|-------------|--------------|----------------|
| admin       | Admin@123    | Administrador  |
| professor   | Usuario@123  | Usuário comum  |

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
│   │   ├── notifications/   # e-mail e WhatsApp
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

## Arquitetura e decisões

O backend segue uma separação por apps de domínio (accounts, environments, reservations,
audit, notifications) desacoplados via Django signals — por exemplo, `reservations` não conhece
diretamente `notifications`; a notificação por e-mail e o evento de WebSocket são disparados
por signals ao salvar uma `Reserva`. Isso mantém os apps coesos e facilita testes e evolução
(Clean Architecture / SOLID aplicados de forma pragmática ao Django).

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
