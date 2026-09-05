# Drop

Envie um arquivo tabular (CSV, Excel, JSON). O Drop perfila os dados, gera um resumo e deixa conversar em português — insights e gráficos com créditos.

Monorepo: API Django (`apps/api`) + web Next.js (`apps/web`).

## Pré-requisitos

- Docker + Docker Compose (Postgres local)
- [uv](https://docs.astral.sh/uv/) e Python 3.12
- Node 20+ e [pnpm](https://pnpm.io/)
- [make](https://www.gnu.org/software/make/) (Git Bash, scoop ou chocolatey). Sem make: `.\scripts\dev-up.ps1`

## Subir local

```powershell
copy .env.example .env
# OPENAI_API_KEY / GEMINI_API_KEY — necessários para overview, chat, insights
# GOOGLE_OAUTH_* — opcional; sem as duas, o botão Google some do /login

make dev
```

Isso sobe o Postgres no Compose (`drop` / `drop` / `drop`), roda migrate e seed. Em **dois terminais**:

```text
make api
make web
```

- Web: http://localhost:3000
- API: http://localhost:8000/health/
- OpenAPI: http://localhost:8000/api/schema/swagger-ui/

`DROP_ENV=local` (default): fila inline, email só no console, arquivos em `var/uploads/`. `DATABASE_URL` no `.env` é ignorado — o banco é o Compose.

Sem make: `.\scripts\dev-up.ps1`. API+DB no Docker: `make up`. Inclui a web (imagem de produção): `make up-full`.

## Como testar

### Automático

```text
make test
```

Ruff + pytest da API (CI mocka o LLM; não chama OpenAI/Gemini/Resend).

Web (em `apps/web`): `pnpm lint`, `pnpm typecheck`, `pnpm build`.

### Manual (fluxo feliz)

1. Abra http://localhost:3000 e faça upload de um CSV (ou um sample da landing).
2. A análise anônima mostra o resumo. Chat / insights / gráficos IA pedem login.
3. Em `/login`, peça o magic link. O email **não** sai: o atalho `dev_verify_url` aparece na tela e o link também no log da API.
4. Com as keys de LLM no `.env`, gere overview, uma pergunta no chat e um insight.

Para parar o Postgres: `make down`.

## Makefile

| Target | Ação |
|--------|------|
| `make dev` | Postgres + migrate + seed |
| `make api` / `make web` | API e Next no host |
| `make test` | ruff + pytest |
| `make up` / `make up-full` | stack Docker |
| `make down` / `make logs` | para / logs |

## Estrutura

```
apps/api         Django + DRF (uv)
apps/web         Next.js + shadcn
packages/ai      LLM OpenAI / Gemini
packages/agents  AgentRunner (ADK depois)
infra/cloudbuild
```

## Docs

- [Documento base](docs/BASE_DO_PROJETO.md)
- [Desenvolvimento local](docs/architecture/local-dev.md) (env, `DROP_ENV`, LLM)
- [Deploy](docs/runbooks/deploy.md)
- [AGENTS.md](AGENTS.md)
