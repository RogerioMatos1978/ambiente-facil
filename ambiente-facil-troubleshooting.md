# Ambiente Fácil — Guia de execução (dev e produção/intranet) + diário de bugs

Repositório: https://github.com/RogerioMatos1978/ambiente-facil
Última atualização: 19/07/2026

---

## Parte 1 — Rodando em DESENVOLVIMENTO

```bash
git clone https://github.com/RogerioMatos1978/ambiente-facil.git
cd ambiente-facil
cp .env.example .env
docker compose up --build
```

Depois que os containers subirem:
```bash
docker compose exec backend python manage.py migrate
docker compose exec backend python manage.py seed_demo
```

Acessos:
- Frontend: http://localhost:3000
- Backend / Swagger: http://localhost:8000/api/docs
- Admin: http://localhost:8000/admin
- Login de teste: `admin` / `Admin@123` (administrador) ou `professor` / `Usuario@123` (usuário comum)

### Bugs encontrados e corrigidos (dev)

**1. `backend-1` em loop de restart.**
Causa: `docker-compose.yml` monta `./backend:/app` (bind mount), sobrescrevendo a pasta `/app/logs` criada no build da imagem. Como `backend/logs` não existe no host, o Django falhava ao configurar o `RotatingFileHandler`:
```
FileNotFoundError: [Errno 2] No such file or directory: '/app/logs/ambiente_facil.log'
ValueError: Unable to configure handler 'file'
```
Correção — `command` do serviço `backend` em `docker-compose.yml`:
```yaml
command: >
  sh -c "mkdir -p logs &&
         python manage.py migrate &&
         daphne -b 0.0.0.0 -p 8000 config.asgi:application"
```

**2. Painel "Reservas em tempo real" preso em "Desconectado".**
Causa: bug de compatibilidade entre `channels-redis==4.2.0` e o `redis-py` instalado — a escuta do grupo Redis (pubsub) estourava timeout de leitura mesmo sem problema de rede, derrubando o WebSocket:
```
redis.exceptions.TimeoutError: Timeout reading from redis:6379
... WSDISCONNECT /ws/painel-ambientes/
```
Correção — `backend/requirements.txt`:
```diff
- channels==4.1.0
- channels-redis==4.2.0
+ channels==4.2.2
+ channels-redis==4.3.0
+ redis==5.0.8
```
Correção complementar — `frontend/src/hooks/use-painel-tempo-real.ts`: adicionada reconexão automática (retry a cada 3s) para o painel se recuperar sozinho de qualquer soluço futuro do Redis, sem precisar recarregar a página.

**Observação:** também apareceu um container backend órfão (`gifted_diffie`) de um `docker compose up` anterior sem `down`. Limpar com `docker rm -f <nome-do-container>`.

---

## Parte 2 — Rodando em PRODUÇÃO na rede interna (intranet, sem acesso externo)

Cenário: um PC na rede local serve o sistema para os outros computadores da mesma rede, sem domínio, sem certificado HTTPS, sem hospedagem externa.

### 2.1 Preparação

1. **Reserve um IP fixo** para o PC servidor no roteador (DHCP reservation) ou configure IP estático no Windows. Se o IP mudar depois, o frontend para de funcionar e precisa ser rebuildado.
2. Descubra o IP com `ipconfig` (exemplo usado neste guia: `192.168.1.64`).
3. Libere a porta **80** no Firewall do Windows para rede privada (Docker Desktop costuma pedir isso na primeira subida).

### 2.2 Arquivos que precisaram ser corrigidos

O `docker-compose.prod.yml` original do repositório tinha 2 lacunas conhecidas (o próprio comentário do arquivo avisava) e os `Dockerfile.prod` tinham 2 bugs não documentados. Todos foram corrigidos:

**`docker-compose.prod.yml`**
- Backend trocou de `gunicorn config.wsgi:application` (WSGI puro) para `gunicorn config.asgi:application -k uvicorn.workers.UvicornWorker` (ASGI) — sem isso, o WebSocket do painel em tempo real não funciona em produção, só a API REST.
- `DJANGO_SETTINGS_MODULE` mudou de `config.settings.prod` para `config.settings.lan` (novo módulo, ver abaixo).
- Serviço `frontend` ganhou `build: args: NEXT_PUBLIC_API_URL` — variável `NEXT_PUBLIC_*` do Next.js é embutida no JavaScript **no momento do build**, não em tempo de execução; só declarar em `environment:` não bastava.

**`backend/config/settings/lan.py` (novo arquivo)**
Desativa as exigências de HTTPS do `prod.py` original (`SECURE_SSL_REDIRECT`, `SESSION_COOKIE_SECURE`, `CSRF_COOKIE_SECURE`), já que a intranet não tem certificado. Sem isso, login e CSRF quebravam (o navegador não envia cookies "secure" em conexão HTTP simples).

**`backend/Dockerfile.prod`**
Bug: pacotes Python eram instalados com `pip install --user` rodando como `root` (vão para `/root/.local`), mas o container roda como usuário `appuser` (home em `/home/appuser`). Resultado: Django nem era encontrado.
```
ModuleNotFoundError: No module named 'django'
```
Correção: copiar os pacotes para `/home/appuser/.local` e ajustar `PATH`/dono antes de trocar para `USER appuser`.

**`frontend/Dockerfile.prod`**
Bug: `COPY --from=builder /app/public ./public` falhava porque o repositório não tem pasta `frontend/public`. Correção: `RUN mkdir -p public` garantindo que a pasta sempre exista no build, mesmo vazia.

### 2.3 Configuração do `.env` de produção

Pontos que causaram erro até chegarem certos:

```bash
# ERRADO — ALLOWED_HOSTS não aceita esquema (http://), só o host/IP puro,
# senão o Django rejeita tudo com "DisallowedHost".
DJANGO_ALLOWED_HOSTS=http://192.168.1.64
# CERTO:
DJANGO_ALLOWED_HOSTS=192.168.1.64,localhost,127.0.0.1

# ERRADO — faltando o esquema http://, o navegador não monta a URL da API
# corretamente e a requisição nunca chega no backend.
NEXT_PUBLIC_API_URL=192.168.1.64
# CERTO — sem porta no final (o Nginx na porta 80 já encaminha /api/
# internamente para o backend; a porta 8000 não fica exposta ao host):
NEXT_PUBLIC_API_URL=http://192.168.1.64

# CORS/CSRF, ao contrário de ALLOWED_HOSTS, PRECISAM do esquema:
CORS_ALLOWED_ORIGINS=http://192.168.1.64
CSRF_TRUSTED_ORIGINS=http://192.168.1.64
```

Também trocado: `DJANGO_SECRET_KEY` (o valor de exemplo do repo é inseguro) por uma chave gerada com:
```bash
python -c "import secrets; print(secrets.token_urlsafe(50))"
```

### 2.4 Deploy

```bash
docker compose -f docker-compose.prod.yml up -d --build
```

Migrações e `collectstatic` rodam automaticamente no `command` do backend.

- Teste local: `http://localhost`
- Teste de outro PC da rede: `http://192.168.1.64` (o IP fixo reservado)

**Regra prática para saber se precisa rebuild:**
- Mudou `.env` (senhas, `ALLOWED_HOSTS`, `CORS`, `SECRET_KEY`, etc. — lidos em tempo de execução): só reiniciar, sem `--build`.
  ```bash
  docker compose -f docker-compose.prod.yml up -d backend
  ```
- Mudou `NEXT_PUBLIC_API_URL` (embutido no build do Next.js): precisa rebuild do frontend.
  ```bash
  docker compose -f docker-compose.prod.yml up -d --build frontend
  ```
- Mudou `requirements.txt`, `Dockerfile.prod` ou `docker-compose.prod.yml`: rebuild geral.
  ```bash
  docker compose -f docker-compose.prod.yml up -d --build
  ```

### 2.5 Para sobreviver a reinícios do PC

- Ative "Start Docker Desktop when you sign in" nas configurações do Docker Desktop.
- Todos os serviços já têm `restart: always` no `docker-compose.prod.yml` — voltam sozinhos quando o Docker reinicia.

### 2.6 Backup

Agendar `pg_dump` periódico do volume `postgres_data` (cron/Agendador de Tarefas do Windows), mesmo sem internet — é o único lugar onde os dados moram.

---

## Status atual

✅ Ambiente de desenvolvimento: rodando.
✅ Ambiente de produção na intranet: rodando 100%, acessível pelos PCs da rede local via `http://192.168.1.64`.

Este documento cobre os problemas do deploy inicial (dev + intranet). Depois desse primeiro
deploy, o sistema recebeu várias rodadas de novas funcionalidades e correções — resumidas na
seção abaixo. Sempre que aparecer algo em produção que não bate com o que está descrito aqui
(ex.: uma tela mostrando um campo que a documentação diz que não existe mais), o motivo quase
sempre é **deploy desatualizado**, não bug: veja a regra de rebuild-vs-restart na seção 2.4.

---

## Changelog — funcionalidades e correções após o deploy inicial

Resumo das mudanças entregues depois da primeira subida em produção, para referência rápida de
"o que mudou desde então". Ordem cronológica.

**QR code apontando para `localhost` no celular.** Causa: variável `FRONTEND_URL` ausente do
`.env` de produção (nunca tinha sido adicionada) — sem ela o backend monta o link do QR code com
o endereço padrão de desenvolvimento. Corrigido preenchendo `FRONTEND_URL=http://<IP-DO-PC>` no
`.env` e recriando o container (`--force-recreate`, não `restart` — ver seção 2.4/regra de
rebuild).

**Página de Relatórios (`/relatorios`).** Nova tela com KPIs (total de reservas, confirmadas,
taxa de no-show, duração média), gráfico de reservas por dia, reservas por status, ranking de
ambientes mais reservados e — só para administradores — ranking de quem mais reservou. Tudo
filtrável por período/ambiente/status e exportável em CSV/Excel/PDF (`GET
/api/v1/reservations/relatorio/`).

**Seletor de cores institucionais (5 temas SESI/SENAI/IEL Goiás).** Ícone de paleta na barra
superior com 5 temas baseados no Manual de Marcas do Sistema FIEG (ago/2024): SESI SENAI
(padrão, azul `#164194`), SESI (detalhe verde `#52AE32`), SENAI (detalhe laranja `#E84910`), IEL
(detalhe verde-água `#6CC2BA`) e Sistema FIEG (detalhe azul claro `#008BD2`). A cor escolhida
troca a cor dominante do sistema inteiro (botões, menu ativo, badges, foco), funciona junto com o
tema claro/escuro e fica salva no navegador de cada usuário (não é uma configuração do servidor).

**Regras de administração de reservas.** Editar, excluir ou cancelar uma reserva já existente
passou a ser **exclusivo de administradores** — qualquer usuário autenticado ainda pode solicitar
(criar) uma reserva normalmente. Reservas cujo período já terminou são concluídas
automaticamente (job em segundo plano, `python manage.py concluir_reservas_passadas`, roda junto
com o job de no-show) e ficam somente leitura a partir daí, mesmo para admin. Mensagens de
WhatsApp agora abrem o **aplicativo do WhatsApp Desktop instalado no computador**
(`whatsapp://send`), não mais o WhatsApp Web no navegador — requer o WhatsApp Desktop instalado
na máquina que aciona o botão.

**Número de controle e duração da reserva.** Toda reserva ganhou um número de controle sequencial
(`RES-000123`, derivado do id) e passou a mostrar sua duração calculada (ex.: `1h30min`) — ambos
aparecem na lista de reservas, na tela de detalhes, no calendário, na página de check-in, na
mensagem de WhatsApp e nas exportações CSV/Excel/PDF.

**Agenda compartilhada.** A lista de reservas passou a mostrar as reservas de **todos os
usuários** para qualquer pessoa autenticada (antes, um usuário comum só via as próprias). A regra
de quem pode editar/cancelar continua exclusiva de administrador — mudou só a visibilidade da
lista, não as permissões de alteração.

**Correção: F5 (atualizar página) derrubava para o login.** Bug de timing na hidratação do
estado de autenticação (Zustand `persist`, que lê do `localStorage` de forma assíncrona): ao
apertar F5, a tela verificava se havia login *antes* do estado terminar de carregar do
armazenamento local, e mandava para `/login` por engano mesmo com sessão válida. Corrigido para
esperar a hidratação terminar antes de decidir se redireciona.

**Correção: reservas sumindo do calendário.** O filtro de período (`data_de`/`data_ate`) usava
critério de "contida no período", então uma reserva que começava antes do início da janela
filtrada (ou terminava depois do fim) desaparecia do calendário mesmo estando visível naquele
intervalo. Corrigido para critério de "sobreposição" (a reserva aparece se tiver qualquer
interseção com o período filtrado) — usado no calendário, no relatório e nas exportações.

**Remoção do campo e-mail / telefone como único contato.** O sistema **não usa mais e-mail em
nenhum lugar**: o campo foi removido do cadastro de usuário, do banco de dados e de toda a
interface. O telefone (WhatsApp) passou a ser obrigatório e é o único dado de contato e o único
canal de notificação — não existe mais envio automático de e-mail ao criar reserva (o sistema
nunca dispara nada sozinho; o WhatsApp é sempre uma ação manual, clicando no botão). Se depois
desta mudança uma tela de produção ainda mostrar uma coluna "E-mail", o deploy está desatualizado
— *rebuild* completo é necessário (mudou modelo de dados + migração de banco), não basta
reiniciar: `docker compose -f docker-compose.prod.yml up -d --build`. Vale conferir se todos os
usuários cadastrados têm telefone preenchido depois da migração, já que o WhatsApp passa a
depender exclusivamente dele.

**Correção: atualizar a página (F5/Ctrl+R) pedia login de novo, mesmo com sessão válida.**
Causa raiz diferente da correção anterior de hidratação (que resolvia o *primeiro* render após o
F5): o backend usa rotação de refresh token (`ROTATE_REFRESH_TOKENS` + `BLACKLIST_AFTER_ROTATION`
em `SIMPLE_JWT`) — cada renovação do access token invalida o refresh token antigo e devolve um
novo. O frontend (`lib/api.ts`) guardava só o novo access token e descartava o novo refresh token,
continuando a usar o antigo (já invalidado). Na renovação seguinte — o que acontece toda vez que o
access token expira, a cada 30 min — o refresh falhava e derrubava para o `/login`. Corrigido para
salvar o refresh token novo devolvido pelo backend a cada renovação.

**Novo: botão "Atualizar site".** Ícone de recarregar na barra superior de toda página do painel
(e na página de check-in/QR code, que fica fora dessa barra) — dá um reload completo da página por
dentro do sistema, sem precisar do atalho do navegador. Disponível para todos os perfis de usuário.
