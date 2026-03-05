# High Availability Baseline

This template ships with HA-oriented defaults for Django API workloads.

## Runtime defaults

- Gunicorn:
  - bounded request recycling (`GUNICORN_MAX_REQUESTS` + jitter)
  - keep-alive enabled (`GUNICORN_KEEPALIVE`)
  - worker tmp dir in shared memory (`GUNICORN_WORKER_TMP_DIR=/dev/shm`)
- Database:
  - persistent pooled connections (`DB_CONN_MAX_AGE`)
  - connection health checks (`DB_CONN_HEALTH_CHECKS`)
  - optional PostgreSQL connect/statement timeouts
- Celery:
  - late ack + reject on worker loss
  - bounded worker lifetime (`CELERY_MAX_TASKS_PER_CHILD`)
  - soft/hard task time limits

## Kubernetes baseline

- Web deployment uses rolling updates with `maxUnavailable: 0`.
- Readiness/liveness/startup probes are enabled.
- Web pods are spread with anti-affinity/topology constraints.
- PDBs exist for web and worker workloads.
- HPA scales by CPU and memory with scale-down stabilization.
- Network policies cover web and async workloads.
