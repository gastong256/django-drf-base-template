# Kubernetes Base Manifests

These manifests provide a production-ready baseline for:

- Web API deployment
- Celery worker deployment
- Celery beat scheduler
- Horizontal autoscaling (web)
- Pod disruption budget
- Service + ingress
- Network policy

## Usage

1. Replace placeholders (`__PROJECT_SLUG__`, `__SERVICE_NAME__`, `__PORT__`).
2. Create a secret named `__PROJECT_SLUG__-secrets` with sensitive env vars
   (see `secret.example.yaml`).
3. Apply manifests:

```bash
kubectl apply -f deploy/k8s/
```
