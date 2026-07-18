# Ambiente Fácil — Diário de troubleshooting local (Docker)

Repositório: https://github.com/RogerioMatos1978/ambiente-facil
Data: 17-18/07/2026

## Como rodar localmente (resumo)

```bash
git clone https://github.com/RogerioMatos1978/ambiente-facil.git
cd ambiente-facil
cp .env.example .env
docker compose up --build
docker compose exec backend python manage.py migrate
docker compose exec backend python manage.py seed_demo
```

- Frontend: http://localhost:3000
- Backend / Swagger: http://localhost:8000/api/docs
- Admin: http://localhost:8000/admin
- Login de teste: `admin` / `Admin@123`

## Problema 1 — backend-1 em loop de restart

**Sintoma:** container `backend-1` ficava reiniciando, nunca subia.

**Causa:** `docker-compose.yml` monta `./backend:/app` (bind mount para hot-reload), o que sobrescreve a pasta `/app/logs` criada durante o build da imagem. Como `backend/logs` não existe no host, o Django falhava ao configurar o `RotatingFileHandler` de logging:

```
FileNotFoundError: [Errno 2] No such file or directory: '/app/logs/ambiente_facil.log'
ValueError: Unable to configure handler 'file'
```

**Correção:** `command` do serviço `backend` no `docker-compose.yml` passou a criar a pasta antes de subir:

```yaml
command: >
  sh -c "mkdir -p logs &&
         python manage.py migrate &&
         daphne -b 0.0.0.0 -p 8000 config.asgi:application"
```

## Problema 2 — painel "Reservas em tempo real" preso em "Desconectado"

**Sintoma:** dashboard carregava normalmente, mas o painel WebSocket (`/ws/painel-ambientes/`) aparecia sempre como Desconectado.

**Causa:** bug de compatibilidade conhecido entre `channels-redis==4.2.0` e a versão do `redis-py` instalada — a escuta do grupo Redis (`pubsub`) estourava timeout de leitura mesmo sem problema real de rede, derrubando a conexão WebSocket:

```
redis.exceptions.TimeoutError: Timeout reading from redis:6379
... WSDISCONNECT /ws/painel-ambientes/
```

Não era problema de autenticação JWT nem de código de negócio — o middleware de auth e o consumer (`PainelAmbientesConsumer`) estão corretos.

**Correção (`backend/requirements.txt`):**

```diff
- channels==4.1.0
- channels-redis==4.2.0
+ channels==4.2.2
+ channels-redis==4.3.0
+ redis==5.0.8
```

(`channels-redis 4.3.0` exige `channels>=4.2.2` — versão inicial `4.1.0` gerava conflito de dependências no `pip install`.)

**Correção complementar (`frontend/src/hooks/use-painel-tempo-real.ts`):** adicionada reconexão automática (retry a cada 3s) para que, mesmo que o Redis tenha um soluço momentâneo em produção, o painel se recupere sozinho em vez de exigir reload manual da página.

## Observação à parte

Havia um container backend órfão (`gifted_diffie`, mesma imagem, sem porta exposta) rodando em paralelo — resquício de um `docker compose up` anterior sem `down`. Recomendado limpar com:

```bash
docker rm -f gifted_diffie
```

## Como aplicar as correções

1. Substituir `docker-compose.yml`, `backend/requirements.txt` e `frontend/src/hooks/use-painel-tempo-real.ts` pelos arquivos corrigidos.
2. Rebuild do backend (mudou dependência Python):
   ```bash
   docker compose up -d --build backend
   ```
3. Frontend não precisa rebuild (hot-reload do `next dev`).
