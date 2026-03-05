# __PROJECT_NAME__

> __DESCRIPTION__

**Owner:** __OWNER__

---

## Table of Contents

- [Using This Template](#using-this-template)
- [Quickstart](#quickstart)
- [Local Dev Workflow](#local-dev-workflow)
- [API Docs](#api-docs)
- [Project Structure](#project-structure)
- [Configuration](#configuration)
- [Observability](#observability)
- [Multi-tenancy](#multi-tenancy)
- [OpenTelemetry](#opentelemetry)
- [Async Workers & HA](#async-workers--ha)
- [Runbooks](#runbooks)
- [Releases & Conventional Commits](#releases--conventional-commits)
- [Contributing](#contributing)

---

## Using This Template

1. Click **"Use this template"** on GitHub to create a new repository.
2. Clone your new repository.
3. Run the bootstrap script:

```bash
make init
```

`make init` prompts for project details, replaces all placeholders, renames files, installs dependencies, and sets up pre-commit hooks. After it completes the project is immediately runnable.

---

## Quickstart

**Prerequisites:** Python 3.12+, [uv](https://docs.astral.sh/uv/), Docker + Docker Compose.

```bash
# 1. Start the database
docker compose up -d postgres

# Optional: start redis if you enable READINESS_CHECK_REDIS or run Celery
docker compose --profile redis up -d redis

# 2. Apply migrations
make migrate

# 3. Run the dev server
make run
```

The API is now available at `http://localhost:__PORT__`.

```bash
# Liveness check
curl http://localhost:__PORT__/healthz

# Readiness check
curl http://localhost:__PORT__/readyz

# Ping
curl http://localhost:__PORT__/api/v1/ping

# Create a local API user once (idempotent)
uv run python manage.py shell -c "from django.contrib.auth import get_user_model; User = get_user_model(); User.objects.filter(username='apiuser').exists() or User.objects.create_user('apiuser', password='change-me')"

# Bootstrap default API roles and grant model permissions
uv run python manage.py bootstrap_roles

# Assign writer role to apiuser
uv run python manage.py shell -c "from django.contrib.auth import get_user_model; from django.contrib.auth.models import Group; user = get_user_model().objects.get(username='apiuser'); user.groups.add(Group.objects.get(name='api_writer'))"

# Obtain JWT token pair
TOKEN=$(curl -s -X POST http://localhost:__PORT__/api/v1/auth/token \
  -H "Content-Type: application/json" \
  -d '{"username":"apiuser","password":"change-me"}' | python3 -c 'import json,sys; print(json.load(sys.stdin)["access"])')

# Create an item
curl -s -X POST http://localhost:__PORT__/api/v1/items \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name": "Widget", "description": "A useful widget."}' | python3 -m json.tool

# Retrieve an item (replace <id> with the UUID from above)
curl -H "Authorization: Bearer $TOKEN" http://localhost:__PORT__/api/v1/items/<id>

# Get current user profile + roles
curl -H "Authorization: Bearer $TOKEN" http://localhost:__PORT__/api/v1/auth/me
```

---

## Local Dev Workflow

```bash
make lint          # ruff linter
make format        # black formatter
make typecheck     # pyright
make test          # pytest
make test-cov      # pytest + coverage report
make shell         # Django shell
make migrate       # apply migrations
make makemigrations ARGS="example"  # create migrations for an app
make pre-commit    # run all pre-commit hooks
make celery-worker # run worker
make celery-beat   # run scheduler
make celery-flower # run Flower UI
```

**Adding a new app:**

```bash
uv run python manage.py startapp myapp apps/myapp
```

Follow the pattern in `apps/example/` — add `services.py`, `selectors.py`, `api/`.

---

## API Docs

| URL | Description |
|-----|-------------|
| `/api/openapi.json` | OpenAPI 3.1 schema |
| `/api/docs` | Swagger UI |
| `/api/redoc` | Redoc |

The Postman collection and environment are in `postman/`.

---

## Project Structure

```
apps/               Bounded-context Django apps
  accounts/         Custom user model (UUID), auth endpoints, role permissions
  tenants/          Tenant model + tenant-aware base classes/managers
  example/          Reference implementation — copy this pattern for new apps
    api/            HTTP layer: serializers, views, urls
    models.py       Data model
    services.py     Write-side business logic
    selectors.py    Read-side query logic
    tasks.py        Async task examples (Celery)
config/             Django project (not an app)
  middleware/       RequestID + Tenant middleware
  settings/         base / local / test / prod
  context.py        ContextVars: request_id, tenant_id, tenant_pk
  logging.py        structlog configuration
  otel.py           Optional OpenTelemetry setup
  exceptions.py     DRF custom exception handler
docs/adr/           Architecture Decision Records
docs/runbooks/      Incident + rollback operational guides
tests/              Top-level pytest suite
scripts/            Tooling scripts
postman/            Postman collection + environment
deploy/k8s/         Kubernetes baseline manifests (web/worker/beat/HPA/PDB/Ingress)
```

---

## Configuration

All configuration is environment-based (12-factor). Copy `.env.example` to `.env` and adjust values.

`DJANGO_SETTINGS_MODULE` selects the settings file:

| Value | Use |
|-------|-----|
| `config.settings.local` | Local development (default) |
| `config.settings.test` | Test runner (set in `pyproject.toml`) |
| `config.settings.prod` | Production |

See `.env.example` for all supported variables.

---

## Observability

See [docs/observability.md](docs/observability.md) for full details.

- **Logs**: JSON to stdout (structlog). Includes `request_id`, `tenant_id`, `service`, `environment`, and OTel trace IDs when available.
- **Redaction**: sensitive fields (`password`, `token`, `authorization`, `secret`) are masked automatically.
- **Request ID**: `X-Request-ID` header, auto-generated if missing, echoed in response.
- **Health**: `GET /healthz` (liveness), `GET /readyz` (readiness + DB + optional Redis check).
- **Metrics**: optional internal `GET /metrics` endpoint protected by CIDR/token.
- **Sentry**: optional error tracking via `SENTRY_DSN`.

---

## Multi-tenancy

See [ADR 0002](docs/adr/0002-multitenancy-strategy.md) for the full strategy.

- Tenant resolution is header-based: `X-Tenant-ID: my-tenant` (defaults to `"public"`).
- Tenants are persisted in `apps.tenants.Tenant`; inactive or unknown tenants return `400 invalid_tenant`.
- Data is isolated with a tenant foreign key (`shared schema + tenant column`) in domain models.
- `tenant_id` appears in all log records automatically.

---

## OpenTelemetry

OTel is disabled by default with zero overhead when off. To enable:

```bash
uv sync --extra otel

export OTEL_ENABLED=true
export OTEL_SERVICE_NAME=__SERVICE_NAME__
export OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4317
```

---

## Async Workers & HA

- Celery app is configured under `config/celery.py` and discovers tasks automatically.
- Docker Compose profiles:
  - `docker compose --profile worker up -d` starts worker + beat + redis.
  - `docker compose --profile flower up -d` starts Flower UI (port `5555`).
- Production gunicorn can be tuned via env vars (`GUNICORN_WORKERS`, `GUNICORN_THREADS`, `GUNICORN_MAX_REQUESTS`, etc.).
- Kubernetes baseline manifests are available in `deploy/k8s/`.

---

## Runbooks

- Incident triage and response: [`docs/runbooks/incident-response.md`](docs/runbooks/incident-response.md)
- Rollback procedure: [`docs/runbooks/rollback.md`](docs/runbooks/rollback.md)

---

## Releases & Conventional Commits

Releases are automated via [python-semantic-release](https://python-semantic-release.readthedocs.io/) on every merge to `main`.

| Commit prefix | Version bump |
|---------------|-------------|
| `fix:` | patch (0.0.x) |
| `feat:` | minor (0.x.0) |
| `feat!:` / `BREAKING CHANGE:` | major (x.0.0) |
| `chore:`, `docs:`, `test:`, `refactor:` | no release |

Examples:

```
feat: add user authentication endpoint
fix: correct pagination off-by-one error
feat!: remove legacy v0 API endpoints
```

---

## Contributing

1. Branch from `main`: `git checkout -b feat/my-feature`
2. Follow the [service layer pattern](docs/adr/0003-service-layer-pattern.md).
3. Add tests — `make test` must pass.
4. Use Conventional Commits.
5. Open a PR against `main`.
