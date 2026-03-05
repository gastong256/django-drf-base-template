# ADR 0002: Multitenancy Strategy

**Status:** Accepted
**Date:** 2026-03-05

## Context

The service may need to serve multiple tenants from a single deployment. We need a strategy that is lightweight enough not to impede single-tenant deployments but extensible enough to support true data isolation when required.

## Decision

We adopt **shared schema + tenant column** as the default strategy, with header-based resolution:

1. `TenantMiddleware` reads the `X-Tenant-ID` request header.
2. If absent, `tenant_id` defaults to `"public"`.
3. Tenant identifiers are validated against the `Tenant` table; invalid/inactive tenants are rejected with HTTP 400.
4. `tenant_id` is stored in a `ContextVar` so it is accessible throughout the request lifecycle.
5. Domain models use a tenant foreign key to enforce data isolation in application queries.

This approach keeps operational simplicity while providing real data isolation boundaries at the application layer. Teams can still evolve to stronger isolation with:

- **Shared schema + tenant column**: Add a `tenant_id` FK/field to models and use a global queryset filter (Django managers or a middleware-driven queryset mixin).
- **Schema-per-tenant**: Use `django-tenants` or a custom PostgreSQL `SET search_path` approach per request.
- **Database-per-tenant**: Dynamically route `DATABASES` based on the resolved `tenant_id`.

## Consequences

- All log records include `tenant_id`.
- Data access in selectors/services can be safely scoped by tenant-aware managers/querysets.
- A default `public` tenant is seeded in migrations for single-tenant deployments.
- `X-Tenant-ID` remains untrusted input; gateways or service meshes should still inject verified headers in production.
