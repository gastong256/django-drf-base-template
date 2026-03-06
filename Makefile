.DEFAULT_GOAL := help
.PHONY: help init run test lint format typecheck migrate makemigrations shell docker-build celery-worker celery-beat celery-flower check-deploy audit-code audit-deps security

PYTHON := uv run python
MANAGE := $(PYTHON) manage.py

help:
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

init: ## Bootstrap project: replace placeholders, install deps + pre-commit hooks
	@bash scripts/bootstrap.sh

run: ## Start local development server
	$(MANAGE) runserver 0.0.0.0:$${PORT:-8000}

celery-worker: ## Start Celery worker
	uv run celery -A config worker -l INFO --concurrency=$${CELERY_CONCURRENCY:-2}

celery-beat: ## Start Celery beat scheduler
	uv run celery -A config beat -l INFO

celery-flower: ## Start Flower UI for Celery
	uv run celery -A config flower --port=$${FLOWER_PORT:-5555}

test: ## Run test suite
	uv run pytest $(ARGS)

test-cov: ## Run tests with coverage report
	uv run pytest --cov --cov-report=term-missing $(ARGS)

lint: ## Run ruff linter
	uv run ruff check .

lint-fix: ## Run ruff with auto-fix
	uv run ruff check --fix .

format: ## Run black formatter
	uv run black .

format-check: ## Check formatting without modifying files
	uv run black --check .

typecheck: ## Run pyright type checker
	uv run pyright

migrate: ## Apply database migrations
	$(MANAGE) migrate

makemigrations: ## Create new migrations
	$(MANAGE) makemigrations $(ARGS)

shell: ## Open Django shell
	$(MANAGE) shell

shell-plus: ## Open Django shell_plus (requires django-extensions)
	$(MANAGE) shell_plus

collectstatic: ## Collect static files
	$(MANAGE) collectstatic --noinput

docker-build: ## Build production Docker image
	docker build -t __SERVICE_NAME__:local .

docker-up: ## Start docker-compose services
	docker compose up -d

docker-up-worker: ## Start web + postgres + redis + worker + beat
	docker compose --profile worker up -d

docker-up-flower: ## Start Flower + dependencies
	docker compose --profile flower up -d

docker-down: ## Stop docker-compose services
	docker compose down

docker-logs: ## Tail docker-compose logs
	docker compose logs -f

export-schema: ## Export OpenAPI schema to file
	@bash scripts/export_schema.sh

pre-commit: ## Run pre-commit hooks against all files
	uv run pre-commit run --all-files

check-deploy: ## Run Django deploy checks with secure production defaults
	DJANGO_SETTINGS_MODULE=config.settings.prod \
	DJANGO_SECRET_KEY=check-deploy-secret-key-2026-03-06-4f7a9c2d8e1b5a3c6d9f0e7a1b2c3d4e \
	DJANGO_ALLOWED_HOSTS=api.example.com \
	CSRF_TRUSTED_ORIGINS=https://api.example.com \
	DATABASE_URL=postgres://postgres:postgres@localhost:5432/check_deploy \
	uv run python manage.py check --deploy --fail-level WARNING

audit-code: ## Run static security scan (Bandit)
	uv run bandit -c pyproject.toml -r apps config

audit-deps: ## Run dependency vulnerability audit
	uv run pip-audit

security: ## Run all security checks
	$(MAKE) audit-code
	$(MAKE) audit-deps
	$(MAKE) check-deploy
