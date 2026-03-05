# Kubernetes Base Manifests

These manifests provide a production-ready baseline for:

- Web API deployment
- Celery worker deployment
- Celery beat scheduler
- Horizontal autoscaling (web)
- Pod disruption budgets (web + worker)
- Service + ingress
- Network policies (web + async workers)
- Rolling updates with zero-downtime defaults
- Pod spread/anti-affinity for higher availability
- Runtime hardening (`seccomp`, dropped Linux capabilities)

## Usage

1. Replace placeholders (`__PROJECT_SLUG__`, `__SERVICE_NAME__`, `__PORT__`).
2. Create a secret named `__PROJECT_SLUG__-secrets` with sensitive env vars
   (see `secret.example.yaml`).
3. Apply manifests:

```bash
kubectl apply -f deploy/k8s/
```

## Recommended rollout order

```bash
kubectl apply -f deploy/k8s/configmap.yaml
kubectl apply -f deploy/k8s/secret.example.yaml
kubectl apply -f deploy/k8s/service.yaml
kubectl apply -f deploy/k8s/deployment-web.yaml
kubectl apply -f deploy/k8s/deployment-worker.yaml
kubectl apply -f deploy/k8s/deployment-beat.yaml
kubectl apply -f deploy/k8s/pdb.yaml
kubectl apply -f deploy/k8s/pdb-worker.yaml
kubectl apply -f deploy/k8s/hpa.yaml
kubectl apply -f deploy/k8s/networkpolicy.yaml
kubectl apply -f deploy/k8s/networkpolicy-async.yaml
kubectl apply -f deploy/k8s/ingress.yaml
```
