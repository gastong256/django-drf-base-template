# Rollback Runbook

## Preconditions

- Confirm the current release introduced regression.
- Identify last known good image tag/version.
- Ensure DB compatibility for rollback target.

## Kubernetes Rollback

1. Inspect rollout history:
   ```bash
   kubectl rollout history deployment/__PROJECT_SLUG__-web
   ```
2. Roll back web deployment:
   ```bash
   kubectl rollout undo deployment/__PROJECT_SLUG__-web
   ```
3. If needed, roll back workers:
   ```bash
   kubectl rollout undo deployment/__PROJECT_SLUG__-worker
   kubectl rollout undo deployment/__PROJECT_SLUG__-beat
   ```
4. Verify:
   - Pod readiness
   - `GET /readyz`
   - Sentry/log error trends

## Data Safety Rules

1. Never roll back DB schema blindly after destructive migrations.
2. If migration is irreversible, deploy hotfix instead of schema rollback.
3. Coordinate rollback with database owner before executing.

## Validation Checklist

1. Error rate normal.
2. Authentication and critical endpoints functional.
3. Celery queue processing resumes normally.
4. Incident channel updated with completion timestamp.
