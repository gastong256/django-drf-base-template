# Incident Response Runbook

## Scope

Use this runbook for production incidents affecting availability, latency, or data integrity.

## Severity Levels

- `SEV-1`: Full outage, data loss risk, or major security impact.
- `SEV-2`: Partial outage or severe degradation.
- `SEV-3`: Non-critical degradation with workaround.

## Immediate Actions

1. Acknowledge incident and assign incident commander.
2. Freeze risky deploys and migrations.
3. Verify service health:
   - `GET /healthz`
   - `GET /readyz`
   - `GET /metrics` (if enabled)
4. Check error spikes (Sentry), log anomalies, and queue backlogs (Celery/Flower).
5. Communicate status every 15 minutes for active incidents.

## Triage Checklist

1. Infrastructure:
   - Pod restarts, OOM kills, node pressure, network policy changes.
   - DB and Redis reachability and latency.
2. Application:
   - Recent release version and migration state.
   - Elevated 5xx, auth failures, invalid tenant errors.
   - Celery retries or dead-letter patterns.
3. Security:
   - Unexpected auth tokens, permission bypass attempts, suspicious IP patterns.

## Mitigation Options

1. Scale web replicas / worker replicas.
2. Disable non-critical background tasks.
3. Roll back to last known good release.
4. Temporarily lower traffic via ingress rate limiting.

## Exit Criteria

- Error rate back to baseline.
- Readiness stable for 30+ minutes.
- Queue backlog drained to normal threshold.
- Stakeholders notified with post-incident summary.

## Postmortem

1. Capture timeline and root cause.
2. Define action items with owners and dates.
3. Add regression tests/alerts/runbook updates.
