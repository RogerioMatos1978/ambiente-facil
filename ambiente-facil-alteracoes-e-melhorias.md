# Ambiente Fácil — Alterações e Melhorias

Histórico consolidado de tudo que foi corrigido e implementado, em ordem cronológica.
Para os comandos Docker usados para aplicar/depurar cada rodada, veja
`ambiente-facil-comandos-docker.md`. Versão atual do sistema: **v15**.

---

## Parte 1 — Deploy inicial (desenvolvimento e produção na intranet)

### Bugs do ambiente de desenvolvimento

**`backend-1` em loop de restart.** O `docker-compose.yml` monta `./backend:/app`, sobrescrevendo
a pasta `/app/logs` criada no build da imagem. Como `backend/logs` não existia no host, o Django
falhava ao configurar o `RotatingFileHandler`. Corrigido criando a pasta no `command` do serviço:
`mkdir -p logs && python manage.py migrate && daphne ...`.

**Painel "Reservas em tempo real" preso em "Desconectado".** Incompatibilidade entre
`channels-redis==4.2.0` e o `redis-py` instalado causava timeout na escuta do grupo Redis, mesmo
sem problema de rede. Corrigido atualizando `channels==4.2.2`, `channels-redis==4.3.0`,
`redis==5.0.8`. Complementado com reconexão automática (retry a cada 3s) no hook
`use-painel-tempo-real.ts`, para o painel se recuperar sozinho de qualquer soluço futuro do Redis.

### Deploy em produção na intranet (sem HTTPS, rede local)

- Backend trocou de `gunicorn config.wsgi:application` (WSGI) para
  `gunicorn config.asgi:application -k uvicorn.workers.UvicornWorker` (ASGI) — sem isso o
  WebSocket do painel em tempo real não funciona em produção, só a API REST.
- Novo `backend/config/settings/lan.py`: desativa exigências de HTTPS (`SECURE_SSL_REDIRECT`,
  `SESSION_COOKIE_SECURE`, `CSRF_COOKIE_SECURE`) do `prod.py` original, já que a intranet não tem
  certificado — sem isso login e CSRF quebravam.
- `docker-compose.prod.yml`: serviço `frontend` ganhou `build.args.NEXT_PUBLIC_API_URL` — variável
  `NEXT_PUBLIC_*` do Next.js é embutida no JS **no momento do build**, não em tempo de execução;
  só declarar em `environment:` não bastava.
- `backend/Dockerfile.prod`: pacotes Python eram instalados com `pip install --user` rodando como
  `root` (iam para `/root/.local`), mas o container roda como `appuser` (`/home/appuser`) —
  Django "sumia" (`ModuleNotFoundError: No module named 'django'`). Corrigido copiando os pacotes
  para `/home/appuser/.local` antes de trocar para `USER appuser`.
- `frontend/Dockerfile.prod`: `COPY --from=builder /app/public ./public` falhava por não existir
  `frontend/public` no repositório. Corrigido com `RUN mkdir -p public` antes do build.
- `.env` de produção: `DJANGO_ALLOWED_HOSTS` não aceita esquema (`http://`), só o host/IP puro;
  `NEXT_PUBLIC_API_URL` precisa do esquema `http://` (ao contrário de `ALLOWED_HOSTS`);
  `CORS_ALLOWED_ORIGINS`/`CSRF_TRUSTED_ORIGINS` também precisam do esquema. `DJANGO_SECRET_KEY` de
  exemplo trocado por uma chave gerada com `secrets.token_urlsafe(50)`.

---

## Parte 2 — Funcionalidades e correções pós-deploy inicial

**QR code apontando para `localhost` no celular.** Faltava `FRONTEND_URL` no `.env` de produção.

**Página de Relatórios (`/relatorios`).** KPIs, taxa de no-show, duração média, reservas por
dia/status, ranking de ambientes e de solicitantes, exportável em CSV/Excel/PDF.

**Seletor de 5 temas de cor institucionais** (SESI/SENAI/IEL Goiás, Manual de Marcas ago/2024),
salvo por navegador de cada usuário.

**Administração de reservas exclusiva de administrador** (editar/excluir/cancelar); qualquer
usuário pode solicitar. Reservas com período encerrado são concluídas automaticamente por job em
segundo plano e ficam somente leitura. WhatsApp passou a abrir o app Desktop instalado
(depois revertido para `wa.me`, ver abaixo).

**Número de controle sequencial** (`RES-000123`) e **duração calculada** em toda reserva —
visível na lista, detalhes, calendário, check-in, WhatsApp e exportações.

**Agenda compartilhada**: qualquer usuário autenticado vê as reservas de todos (antes só via as
próprias). Permissão de editar/cancelar continuou exclusiva de admin.

**Correção: filtro de período fazia reservas sumirem do calendário.** Trocado de critério "contida
no período" para "se sobrepõe ao período" (usado no calendário, relatório e exportações).

**Remoção total do campo e-mail.** Não existe mais em lugar nenhum (modelo, banco, interface).
Telefone/WhatsApp passou a ser obrigatório e é o único canal de contato. Não há mais nenhuma
notificação automática disparada pelo sistema — o WhatsApp é sempre uma ação manual do usuário.

**Duas rodadas de correção do bug "F5 derruba para o login":**
1. Timing da hidratação do Zustand `persist` (lê do `localStorage` de forma assíncrona) —
   corrigido esperando a hidratação terminar antes de decidir redirecionar.
2. Rotação de refresh token (`ROTATE_REFRESH_TOKENS`): o frontend descartava o refresh token novo
   devolvido a cada renovação, continuando a usar o antigo (já invalidado) — corrigido salvando o
   token novo. Depois, um terceiro bug mais sutil: o hook reativo do token (`useSyncExternalStore`)
   é obrigado a usar o snapshot "sem token" na primeiríssima renderização pós-hidratação, mesmo com
   a store já correta por dentro — corrigido lendo `useAuthStore.getState().accessToken`
   diretamente no efeito de redirecionamento, em vez do valor reativo.

**Novo: botão "Atualizar site"** na barra superior — reload completo por dentro do sistema.

---

## Parte 3 — Guarita de Chaves (feature completa, em rodadas)

### Rodada 1 — Base da funcionalidade
- Janela de horário obrigatória **07:00–22:00, mesmo dia** para qualquer reserva.
- Campo obrigatório **"Reservado para"**: categoria (Professor/Instrutor/Cliente/Limpeza/
  Manutenção) + nome + telefone de quem vai usar a sala de fato.
- Texto de instruções da guarita (`Reserva.mensagem_guarita`) nos detalhes de cada reserva.
- Novo app `keys`: modelo `Chave` (uma por ambiente, provisionada automaticamente), ações
  `retirar`/`devolver`/`repor` (o "repor" foi removido depois — ver Rodada 4).
- Novo perfil de usuário **Vigilante** ("Guarita" na interface): acesso restrito só à tela
  `/guarita-chaves`, bloqueado do resto do sistema tanto na navegação quanto na API.
- WhatsApp passou a enviar a mensagem para o telefone do **"Reservado para"**, não do
  solicitante (cai para o solicitante só se o responsável não tiver telefone informado).

### Rodada 2 — Refinamentos de listagem e acesso
- Reservas: ordenação por Nº de controle decrescente, filtro padrão `status=Confirmada`, campos
  de busca (título/descrição/ambiente) e filtro por ambiente/status/período.
- Coluna "Chave" na lista de Reservas.
- Papel Guarita disponível no cadastro de usuário.
- WhatsApp revertido de `whatsapp://send` (app Desktop) para `https://wa.me/...` — funciona com ou
  sem o WhatsApp Desktop instalado — e restrito a reservas com status Confirmada.
- Confirmação de que não sobrou nenhum código de envio de e-mail no sistema.
- Painel em tempo real: texto "Libera às HH:mm" nos cards ocupados + balão com detalhes completos
  ao passar o mouse.

### Rodada 3 — Devolver chave encerra tudo (pedido do usuário)
Antes: devolver só marcava a chave como "devolvida"; um segundo passo manual ("repor") deixava
disponível de novo, e a reserva nunca era encerrada automaticamente.

Mudança: **devolver a chave, num único clique, agora**: (1) encerra a reserva vinculada
(`status = concluída`), (2) libera a sala, (3) deixa a chave direto em "disponível" — sem estado
intermediário.

### Rodada 4 — Correção: reserva não finalizava ao devolver (bug real de produção)
Causa raiz: a notificação em tempo real (WebSocket/Redis) roda **dentro** do próprio
`Reserva.save()`, disparada por signal. Se o Redis estivesse indisponível/instável no ambiente da
guarita, essa notificação lançava uma exceção que interrompia a operação antes da chave ser
liberada — e em alguns cenários revertia até a finalização da reserva.

Correção:
- Notificação em tempo real virou **"melhor esforço"**: qualquer falha nela é capturada e logada,
  nunca mais impede a reserva de ser concluída nem a chave de ser liberada
  (`apps/environments/signals.py`).
- `retirar`/`devolver`/`repor` passaram a rodar em **transação atômica** — reserva e chave mudam
  juntas ou nenhuma muda.
- Lista de Reservas passou a atualizar sozinha via WebSocket sempre que qualquer reserva muda de
  estado (antes só recarregava com F5).
- Teste de regressão adicionado simulando Redis indisponível.

### Rodada 5 — Ação "repor" removida por completo (pedido do usuário)
- **Nenhum perfil** (nem administrador) tem mais acesso a "repor" — a rota foi removida do
  backend, o botão removido do frontend.
- Status "devolvida" removido do modelo `Chave` (migração de dados converte qualquer chave
  porventura parada nesse estado para "disponível"). Só restam dois estados: disponível ↔ ocupada.
- Testes adicionados garantindo a invariante pedida — **nenhuma reserva fica em aberto**: (1) ao
  devolver a chave, a reserva é sempre concluída; (2) mesmo que a chave nunca seja devolvida
  fisicamente, o job `concluir_reservas_passadas` (já existente, roda em segundo plano a cada
  poucos minutos) conclui automaticamente qualquer reserva "pendente"/"confirmada" cujo horário já
  tenha passado, com ou sem chave envolvida.

### Rodada 6 — Alerta de chave atrasada: implementado e depois removido
Foi implementado um alerta automático (job a cada poucos minutos + WebSocket + linha amarela na
lista de Reservas) para avisar quando uma chave passava de 10 minutos sem devolução após o fim da
reserva. **Removido novamente a pedido do usuário** — não faz mais parte do sistema. Removidos:
setting `CHAVE_TOLERANCIA_DEVOLUCAO_MINUTOS`, o management command `alertar_chaves_atrasadas`, o
campo `atraso_notificado_em` (com migração), o campo `chave_atrasada` na API, a linha amarela e o
selo "Atrasada" no frontend.

### Lição de deploy desta rodada (não é bug de código)
Depois de entregar as correções acima, o ambiente de produção continuou mostrando a tela antiga
(botão "Repor", status "Devolvida") mesmo após reconstruir os containers. Causa: **havia duas
cópias da pasta do projeto no PC**, e o `docker-compose.prod.yml` estava sendo executado a partir
da cópia com o código antigo — confirmado pelo log de build do Docker mostrando `COPY . .` como
`CACHED` mesmo com `--build` (BuildKit usa hash de conteúdo: só reaproveita cache se os arquivos
realmente não mudaram). Depois de apontar para a pasta certa e reconstruir, resolveu. Ver
`ambiente-facil-comandos-docker.md` para os comandos de diagnóstico usados para descobrir isso.

---

## Estado atual (v15)

- Ciclo da chave: **disponível → ocupada → disponível**, sem etapas manuais extras, para
  qualquer perfil.
- Nenhuma reserva fica presa "pendente"/"confirmada" para sempre — garantido tanto pela devolução
  manual da chave quanto pelo job automático de conclusão por tempo encerrado.
- Sem alerta de chave atrasada (removido a pedido do usuário).
- Notificações em tempo real (WebSocket) são best-effort: falha nelas nunca quebra uma operação
  de negócio.
- README.md do repositório reflete este estado (checado e corrigido nesta rodada: uma menção
  residual ao status "Devolvida" na lista de recursos foi corrigida).
