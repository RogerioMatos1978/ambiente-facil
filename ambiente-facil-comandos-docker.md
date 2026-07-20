# Ambiente Fácil — Comandos Docker

Referência rápida de todos os comandos usados para rodar, atualizar e depurar o sistema via
Docker. Comandos de PowerShell (Windows) marcados onde diferem do bash/Linux.

---

## 1. Desenvolvimento

```bash
git clone https://github.com/RogerioMatos1978/ambiente-facil.git
cd ambiente-facil
cp .env.example .env
docker compose up --build
```

Depois dos containers subirem:

```bash
docker compose exec backend python manage.py migrate
docker compose exec backend python manage.py seed_demo
```

Acessos: frontend `http://localhost:3000`, API/Swagger `http://localhost:8000/api/docs`,
admin `http://localhost:8000/admin`.

Parar tudo:

```bash
docker compose down
```

---

## 2. Produção (intranet, sem HTTPS)

### 2.1 Subir pela primeira vez / aplicar mudanças de código

```bash
docker compose -f docker-compose.prod.yml up -d --build
```

Migrações e `collectstatic` rodam automaticamente (fazem parte do `command` do serviço backend).

### 2.2 Regra prática: quando reiniciar basta, e quando precisa rebuild

| Mudou... | Comando |
|---|---|
| `.env` (senhas, `ALLOWED_HOSTS`, `CORS`, `SECRET_KEY` — lidos em tempo de execução) | `docker compose -f docker-compose.prod.yml up -d backend` (só restart, sem `--build`) |
| `NEXT_PUBLIC_API_URL` (embutido no build do Next.js) | `docker compose -f docker-compose.prod.yml up -d --build frontend` |
| Código-fonte (backend e/ou frontend), `requirements.txt`, `Dockerfile.prod`, `docker-compose.prod.yml` | rebuild geral, ver 2.3 abaixo |

### 2.3 Rebuild completo e forçado (usar sempre que atualizar o código)

O `--build` sozinho pode reaproveitar cache se o Docker (BuildKit) achar que os arquivos não
mudaram — o que já causou entrega de código desatualizado numa rodada real (ver
`ambiente-facil-alteracoes-e-melhorias.md`, "Lição de deploy"). Sequência mais segura:

```bash
docker compose -f docker-compose.prod.yml down
docker compose -f docker-compose.prod.yml build --no-cache backend frontend
docker compose -f docker-compose.prod.yml up -d
```

Se ainda desconfiar de cache (ex.: precisou trocar imagem base, ou nada do acima resolveu), forma
"nuclear" — remove as imagens do projeto por completo antes de reconstruir:

```bash
docker compose -f docker-compose.prod.yml down --rmi all
docker compose -f docker-compose.prod.yml build --no-cache --pull backend frontend
docker compose -f docker-compose.prod.yml up -d
```

### 2.4 Verificar se os containers realmente são novos

```bash
docker compose -f docker-compose.prod.yml ps
```

Confira a coluna de tempo de criação — deve mostrar algo como "seconds ago"/"About a minute ago"
logo depois do rebuild, não um tempo antigo.

---

## 3. Diagnóstico — "atualizei o código mas a tela continua com a versão antiga"

Ordem recomendada de verificação:

**3.1 — Confirme que o arquivo no disco (fora do Docker) já tem o código novo**, antes de sequer
mexer no Docker. Se isso não mudou, nenhum rebuild vai ajudar.

PowerShell:
```powershell
Select-String -Path "frontend\src\app\(dashboard)\guarita-chaves\page.tsx" -Pattern "Repor"
(Get-Item "frontend\src\app\(dashboard)\guarita-chaves\page.tsx").LastWriteTime
```

Linux/bash:
```bash
grep -n "Repor" "frontend/src/app/(dashboard)/guarita-chaves/page.tsx"
stat -c '%y' "frontend/src/app/(dashboard)/guarita-chaves/page.tsx"
```

**3.2 — Confirme qual pasta o `docker-compose` está de fato usando** (útil se houver mais de uma
cópia do projeto no PC — foi exatamente essa a causa real de um caso de "código antigo"):

```bash
docker compose -f docker-compose.prod.yml config | Select-String "context:"
```
(no Linux, troque `Select-String` por `grep`)

**3.3 — Confirme que não há containers duplicados/antigos disputando a mesma porta** (fora do
projeto atual, ex.: subido manualmente ou de outro `docker-compose`):

```bash
docker ps -a
```

**3.4 — Prova definitiva: olhe o log do build.** Se a camada `COPY . .` aparecer como `CACHED`
mesmo depois de mudar o código-fonte, o Docker está reaproveitando uma imagem cujo conteúdo é
idêntico ao anterior — ou seja, o código "novo" não chegou de fato até ali (normalmente porque o
`docker-compose` está apontando para uma pasta diferente da que foi atualizada — volte ao passo
3.2). Rode o rebuild (seção 2.3) e observe a saída:

```
#13 [frontend builder 4/6] COPY . .
#13 CACHED          ← ruim, sinal de que nada mudou de verdade
```

**3.5 — Prova definitiva de dentro do container já rodando** (depois do rebuild):

```bash
docker compose -f docker-compose.prod.yml exec frontend sh -c "grep -r Repor .next/ || echo SEM_REPOR_OK"
```

**3.6 — Depois de tudo confirmado no backend/Docker, ainda assim confira o navegador**: dê
Ctrl+Shift+R (hard refresh) ou abra em aba anônima, para descartar cache do navegador.

---

## 4. Logs e execução de comandos dentro dos containers

```bash
# logs em tempo real
docker compose -f docker-compose.prod.yml logs -f backend
docker compose -f docker-compose.prod.yml logs -f frontend

# últimas N linhas
docker compose -f docker-compose.prod.yml logs backend --tail 100

# filtrar log (PowerShell)
docker compose -f docker-compose.prod.yml logs backend | Select-String -Pattern "migrat"
# filtrar log (Linux/bash)
docker compose -f docker-compose.prod.yml logs backend | grep -i migrat

# rodar um comando de management dentro do container já rodando
docker compose -f docker-compose.prod.yml exec backend python manage.py migrate
docker compose -f docker-compose.prod.yml exec backend python manage.py concluir_reservas_passadas
docker compose -f docker-compose.prod.yml exec backend python manage.py createsuperuser

# abrir um shell dentro do container
docker compose -f docker-compose.prod.yml exec backend sh
docker compose -f docker-compose.prod.yml exec frontend sh
```

---

## 5. Banco de dados (Postgres)

```bash
# backup manual
docker compose -f docker-compose.prod.yml exec db pg_dump -U <POSTGRES_USER> <POSTGRES_DB> > backup.sql

# restaurar
docker compose -f docker-compose.prod.yml exec -T db psql -U <POSTGRES_USER> <POSTGRES_DB> < backup.sql

# entrar direto no psql
docker compose -f docker-compose.prod.yml exec db psql -U <POSTGRES_USER> <POSTGRES_DB>
```

Agendar o `pg_dump` periodicamente (cron ou Agendador de Tarefas do Windows) — é o único lugar
onde os dados moram, mesmo sem internet.

---

## 6. Limpeza geral (usar com cuidado)

```bash
# remove containers parados, redes e imagens "soltas" (não apaga volumes/dados)
docker system prune

# remove TAMBÉM imagens não usadas por nenhum container (mais agressivo)
docker system prune -a

# apaga containers + imagens do projeto, mantendo o volume do banco (postgres_data)
docker compose -f docker-compose.prod.yml down --rmi all
```

**Nunca** use `docker compose down -v` em produção sem ter certeza — o `-v` apaga também os
volumes nomeados, incluindo `postgres_data` (todos os dados do banco).

---

## 7. Preparar para sobreviver a reinícios do PC

- Ativar "Start Docker Desktop when you sign in" nas configurações do Docker Desktop.
- Todos os serviços já têm `restart: always` no `docker-compose.prod.yml` — voltam sozinhos
  quando o Docker reinicia, sem precisar rodar `up` de novo manualmente.
