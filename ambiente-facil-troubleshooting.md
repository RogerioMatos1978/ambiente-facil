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
