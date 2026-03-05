# Security Baseline

This template includes a default security baseline aligned with production Django services.

## Application hardening

- Production settings (`config.settings.prod`) fail fast if:
  - `DJANGO_SECRET_KEY` is missing/unsafe.
  - `DJANGO_ALLOWED_HOSTS` is unset, wildcarded, or localhost-only.
  - `CORS_ALLOW_ALL_ORIGINS=true`.
  - `DATABASE_URL` resolves to SQLite.
- HTTPS/security headers are enabled in production defaults.
- JWT auth is enabled by default for API endpoints.

## CI/CD checks

The CI workflow validates:

- Lint (`ruff`), format (`black --check`), and type checks (`pyright`)
- Bandit static security scan
- Migration drift (`makemigrations --check --dry-run`)
- Django deployment checks (`manage.py check --deploy --fail-level WARNING`)
- Test suite and coverage (initialized repositories)

## Supply-chain controls

- Weekly Dependabot updates for Python deps and GitHub Actions.
- Dedicated `Security` workflow with:
  - Bandit scan
  - `pip-audit` dependency vulnerability audit

## Local commands

```bash
make audit-code    # bandit
make audit-deps    # pip-audit
make check-deploy  # django check --deploy
make security      # all three
```
