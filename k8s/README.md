# Heretek Swarm - Kubernetes Deployment

This directory contains all Kubernetes manifests for deploying Heretek Swarm to a Kubernetes cluster.

## Prerequisites

- Kubernetes cluster (v1.24+)
- kubectl configured and connected to your cluster
- Helm (optional, for installing additional components)
- Container registry access (for pulling images)

## Quick Start

### 1. Set Environment Variables

Create a `.env` file or export required variables:

```bash
export POSTGRES_PASSWORD=your-secure-password
export OPENAI_API_KEY=your-openai-key
export ANTHROPIC_API_KEY=your-anthropic-key
export QDRANT_API_KEY=your-qdrant-key
export GRAFANA_ADMIN_PASSWORD=your-grafana-password
export JWT_SECRET=your-jwt-secret
export API_KEY=your-api-key
```

### 2. Deploy Using Script

The easiest way to deploy is using the provided deployment script:

```bash
# Deploy all components
./scripts/deploy-k8s.sh

# Use specific kubeconfig context
KUBE_CONTEXT=my-context ./scripts/deploy-k8s.sh
```

### 3. Manual Deployment

Apply manifests in order:

```bash
# 1. Create namespace
kubectl apply -f k8s/namespace.yaml

# 2. Apply secrets (with envsubst for variable substitution)
envsubst < k8s/secrets.yaml | kubectl apply -f -

# 3. Apply configmaps
kubectl apply -f k8s/configmaps.yaml

# 4. Deploy infrastructure
kubectl apply -f k8s/postgres-deployment.yaml
kubectl apply -f k8s/redis-deployment.yaml
kubectl apply -f k8s/qdrant-deployment.yaml

# 5. Wait for infrastructure
kubectl wait --for=condition=ready pod -l app=postgres -n heretek-swarm --timeout=300s
kubectl wait --for=condition=ready pod -l app=redis -n heretek-swarm --timeout=300s
kubectl wait --for=condition=ready pod -l app=qdrant -n heretek-swarm --timeout=300s

# 6. Deploy applications
kubectl apply -f k8s/api-deployment.yaml
kubectl apply -f k8s/dashboard-deployment.yaml
kubectl apply -f k8s/autonomous-deployment.yaml

# 7. Configure autoscaling
kubectl apply -f k8s/hpa.yaml

# 8. Configure ingress (optional)
kubectl apply -f k8s/ingress.yaml
```

## Components

### Infrastructure

| Component | Type | Replicas | Storage |
|-----------|------|-----------|----------|
| PostgreSQL | StatefulSet | 1 | 20Gi |
| Redis | StatefulSet | 1 | 5Gi |
| Qdrant | StatefulSet | 1 | 30Gi |

### Applications

| Component | Type | Replicas | Auto-scaling |
|-----------|------|-----------|--------------|
| API | Deployment | 3 | 3-10 pods |
| Dashboard | Deployment | 2 | 2-5 pods |
| Autonomous Runtime | Deployment | 1 | No |

### Monitoring (Optional)

| Component | Type | Replicas | Storage |
|-----------|------|-----------|----------|
| Prometheus | Deployment | 1 | 20Gi |
| Grafana | Deployment | 1 | 5Gi |

## Accessing Services

### Port Forwarding (Development)

```bash
# API
kubectl port-forward -n heretek-swarm svc/heretek-swarm-api 8000:8000

# Dashboard
kubectl port-forward -n heretek-swarm svc/heretek-swarm-dashboard 3000:80

# Grafana
kubectl port-forward -n heretek-swarm svc/grafana 3001:3000

# Prometheus
kubectl port-forward -n heretek-swarm svc/prometheus 9090:9090
```

### Ingress (Production)

Configure DNS records to point to your ingress controller:

- `api.heretek-swarm.com` → API
- `dashboard.heretek-swarm.com` → Dashboard
- `grafana.heretek-swarm.com` → Grafana (if deployed)

## Scaling

### Manual Scaling

```bash
# Scale API to 5 replicas
kubectl scale deployment/heretek-swarm-api -n heretek-swarm --replicas=5

# Scale Dashboard to 3 replicas
kubectl scale deployment/heretek-swarm-dashboard -n heretek-swarm --replicas=3
```

### Auto-scaling

Horizontal Pod Autoscalers are configured for:

- **API**: 3-10 replicas based on CPU/memory
- **Dashboard**: 2-5 replicas based on CPU/memory

View HPA status:

```bash
kubectl get hpa -n heretek-swarm
```

## Monitoring

### View Logs

```bash
# All pods
kubectl logs -n heretek-swarm -l app=heretek-swarm-api --tail=100

# Specific pod
kubectl logs -n heretek-swarm <pod-name> --tail=100 -f
```

### View Metrics

Access Grafana dashboard for comprehensive monitoring:

1. Port-forward or access via ingress
2. Login with admin credentials
3. Pre-configured dashboards:
   - Heretek Swarm API Overview
   - Infrastructure Health
   - Agent Performance
   - Consciousness Metrics

### Prometheus Alerts

Alerts are configured for:

- API downtime
- High error rates
- High latency
- Database connectivity issues
- Resource usage thresholds

View active alerts:

```bash
kubectl get prometheusrules -n heretek-swarm
```

## Maintenance

### Updates

```bash
# Update deployment image
kubectl set image deployment/heretek-swarm-api \
  api=ghcr.io/heretek-ai/heretek-swarm-api:1.0.1 \
  -n heretek-swarm

# Watch rollout
kubectl rollout status deployment/heretek-swarm-api -n heretek-swarm
```

### Rollbacks

```bash
# Rollback to previous revision
kubectl rollout undo deployment/heretek-swarm-api -n heretek-swarm

# View rollout history
kubectl rollout history deployment/heretek-swarm-api -n heretek-swarm
```

### Cleanup

Use the provided destroy script:

```bash
# Destroy all resources
./scripts/destroy-k8s.sh

# Force destroy without confirmation
FORCE=true ./scripts/destroy-k8s.sh

# Use specific kubeconfig context
KUBE_CONTEXT=my-context ./scripts/destroy-k8s.sh
```

## Troubleshooting

### Pods Not Starting

```bash
# Check pod status
kubectl get pods -n heretek-swarm

# Describe pod for details
kubectl describe pod <pod-name> -n heretek-swarm

# View logs
kubectl logs <pod-name> -n heretek-swarm
```

### Database Connection Issues

```bash
# Check PostgreSQL is ready
kubectl exec -n heretek-swarm postgres-0 -- pg_isready -U heretek

# Test connection from API pod
kubectl exec -n heretek-swarm <api-pod> -- nc -zv postgres 5432
```

### Persistent Volume Issues

```bash
# List PVCs
kubectl get pvc -n heretek-swarm

# Describe PVC
kubectl describe pvc <pvc-name> -n heretek-swarm
```

## Security

### Secrets Management

Production deployments should use:

1. **Kubernetes Secrets** (as configured)
2. **External Secret Manager** (AWS Secrets Manager, Azure Key Vault, etc.)
3. **Sealed Secrets** for GitOps workflows

### Network Policies

Consider adding network policies for:

- Restrict pod-to-pod communication
- Limit ingress access
- Implement service mesh (Istio, Linkerd)

### RBAC

Review and customize RBAC rules in:

- `prometheus-deployment.yaml` - Prometheus cluster role
- Service accounts for each component

## Production Checklist

- [ ] Update all default passwords
- [ ] Configure TLS certificates
- [ ] Set up backup strategy for databases
- [ ] Configure resource limits based on load testing
- [ ] Enable monitoring and alerting
- [ ] Set up log aggregation (ELK, Loki, etc.)
- [ ] Configure disaster recovery
- [ ] Implement security scanning in CI/CD
- [ ] Set up secrets management
- [ ] Configure ingress with proper domains
- [ ] Enable audit logging
- [ ] Set up automated backups
