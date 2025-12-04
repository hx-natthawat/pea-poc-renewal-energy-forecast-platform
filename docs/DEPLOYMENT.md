# PEA RE Forecast Platform - Deployment Guide

## Overview

This guide covers deployment of the PEA RE Forecast Platform to production environments.

## Prerequisites

- Docker 24.x+
- Kubernetes 1.28+
- Helm 3.13+
- kubectl configured with cluster access
- GitLab CI/CD or ArgoCD for GitOps

## Quick Start (Local Development)

```bash
# Clone repository
git clone https://gitlab.pea.co.th/re-forecast/pea-re-forecast.git
cd pea-re-forecast

# Start all services
docker-compose -f docker/docker-compose.yml up -d

# Verify services
curl http://localhost:8000/api/v1/health
curl http://localhost:3000
```

## Production Deployment

### Option 1: Helm Chart Deployment

```bash
# Add Helm repository (if published)
# helm repo add pea-forecast https://charts.pea.co.th/pea-forecast

# Install to Kubernetes
helm upgrade --install pea-forecast ./infrastructure/helm/pea-forecast \
  --namespace pea-forecast \
  --create-namespace \
  -f infrastructure/helm/pea-forecast/values-prod.yaml

# Verify deployment
kubectl get pods -n pea-forecast
kubectl get svc -n pea-forecast
```

### Option 2: ArgoCD GitOps

```yaml
# infrastructure/argocd/application.yaml
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: pea-forecast-production
  namespace: argocd
spec:
  project: default
  source:
    repoURL: https://gitlab.pea.co.th/re-forecast/pea-re-forecast.git
    targetRevision: main
    path: infrastructure/helm/pea-forecast
    helm:
      valueFiles:
        - values-prod.yaml
  destination:
    server: https://kubernetes.default.svc
    namespace: pea-forecast-prod
  syncPolicy:
    automated:
      prune: true
      selfHeal: true
```

```bash
# Apply ArgoCD application
kubectl apply -f infrastructure/argocd/application.yaml
```

### Option 3: Direct Kubernetes Manifests

```bash
# Apply base resources
kubectl apply -f infrastructure/kubernetes/base/

# Apply application deployments
kubectl apply -f infrastructure/kubernetes/apps/backend/
kubectl apply -f infrastructure/kubernetes/apps/frontend/

# Apply database resources
kubectl apply -f infrastructure/kubernetes/databases/timescaledb/
kubectl apply -f infrastructure/kubernetes/databases/redis/
```

## Environment Configuration

### Required Environment Variables

```bash
# Backend (.env)
APP_ENV=production
APP_SECRET_KEY=<generate-secure-key>

# Database
DATABASE_URL=postgresql+asyncpg://<user>:<password>@<host>:5432/pea_forecast

# Redis
REDIS_URL=redis://<host>:6379/0

# Keycloak Authentication
KEYCLOAK_URL=https://auth.pea-forecast.go.th
KEYCLOAK_REALM=pea-forecast
KEYCLOAK_CLIENT_ID=pea-forecast-api
KEYCLOAK_CLIENT_SECRET=<client-secret>

# ML Models
MODEL_REGISTRY_PATH=/app/models
MLFLOW_TRACKING_URI=http://mlflow:5000
```

### Secrets Management (Vault)

```bash
# Store secrets in Vault
vault kv put secret/pea-forecast/prod \
  database_url="postgresql+asyncpg://..." \
  redis_url="redis://..." \
  keycloak_secret="..."

# Reference in Kubernetes
kubectl create secret generic pea-forecast-secrets \
  --from-literal=DATABASE_URL="..." \
  --namespace pea-forecast
```

## Database Setup

### TimescaleDB Initialization

```bash
# Connect to database
kubectl exec -it pea-timescaledb-0 -n pea-forecast -- psql -U postgres

# Run schema
\i /docker-entrypoint-initdb.d/01-schema.sql

# Verify tables
\dt

# Check hypertables
SELECT * FROM timescaledb_information.hypertables;
```

### Data Migration

```bash
# Load POC data
kubectl exec -it pea-backend-xxx -n pea-forecast -- \
  python scripts/load_poc_data.py

# Verify data count
kubectl exec -it pea-timescaledb-0 -n pea-forecast -- \
  psql -U postgres -d pea_forecast -c "SELECT count(*) FROM solar_measurements;"
```

## SSL/TLS Configuration

### Ingress with TLS

```yaml
# infrastructure/kubernetes/ingress/ingress.yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: pea-forecast-ingress
  annotations:
    cert-manager.io/cluster-issuer: letsencrypt-prod
    nginx.ingress.kubernetes.io/ssl-redirect: "true"
spec:
  ingressClassName: nginx
  tls:
    - hosts:
        - pea-forecast.go.th
        - api.pea-forecast.go.th
      secretName: pea-forecast-tls
  rules:
    - host: pea-forecast.go.th
      http:
        paths:
          - path: /
            pathType: Prefix
            backend:
              service:
                name: pea-frontend
                port:
                  number: 3000
    - host: api.pea-forecast.go.th
      http:
        paths:
          - path: /
            pathType: Prefix
            backend:
              service:
                name: pea-backend
                port:
                  number: 8000
```

## Monitoring Setup

### Prometheus & Grafana

```bash
# Deploy observability stack
docker-compose -f docker/docker-compose.observability.yml up -d

# Access Grafana
# URL: http://localhost:3333
# User: admin
# Pass: admin

# Import dashboards from:
# docker/observability/grafana/provisioning/dashboards/
```

### Health Checks

```bash
# API health
curl https://api.pea-forecast.go.th/api/v1/health

# Metrics endpoint
curl https://api.pea-forecast.go.th/metrics

# Database health
kubectl exec -it pea-timescaledb-0 -- pg_isready -U postgres
```

## Security Scanning

### Pre-deployment Security Checks

```bash
# Run Trivy container scan
docker run --rm -v /var/run/docker.sock:/var/run/docker.sock \
  aquasec/trivy:0.48.3 image pea-forecast/backend:latest

# Run SonarQube analysis
docker-compose -f docker/docker-compose.security.yml up -d sonarqube
sonar-scanner -Dsonar.host.url=http://localhost:9000

# Run dependency check
./scripts/security-scan.sh all
```

## Load Testing

### Verify Production Capacity

```bash
# Quick smoke test
./scripts/run-loadtest.sh quick

# Standard load test (500 users)
./scripts/run-loadtest.sh standard

# Full scale test (TOR: 300K users)
./scripts/run-loadtest.sh scale

# Distributed load test
docker-compose -f docker/docker-compose.loadtest.yml up -d
# Open http://localhost:8089 for Locust UI
```

## Rollback Procedures

### Helm Rollback

```bash
# List releases
helm history pea-forecast -n pea-forecast

# Rollback to previous version
helm rollback pea-forecast 1 -n pea-forecast
```

### ArgoCD Rollback

```bash
# View history
argocd app history pea-forecast-production

# Rollback
argocd app rollback pea-forecast-production <revision>
```

### Database Rollback

```bash
# Restore from backup
pg_restore -h localhost -U postgres -d pea_forecast backup.dump

# Or use TimescaleDB continuous aggregates for point-in-time recovery
```

## Troubleshooting

### Common Issues

#### Backend not starting
```bash
# Check logs
kubectl logs -f deployment/pea-backend -n pea-forecast

# Common fixes:
# - Verify DATABASE_URL is correct
# - Ensure database is accessible
# - Check Redis connectivity
```

#### Frontend 502 errors
```bash
# Check ingress
kubectl describe ingress pea-forecast-ingress -n pea-forecast

# Check frontend pods
kubectl get pods -l app=pea-frontend -n pea-forecast
```

#### Database connection issues
```bash
# Test connectivity
kubectl run -it --rm debug --image=postgres:16 -- \
  psql postgresql://user:pass@pea-timescaledb:5432/pea_forecast

# Check TimescaleDB logs
kubectl logs -f pea-timescaledb-0 -n pea-forecast
```

### Support Contacts

- DevOps Team: devops@pea.co.th
- Platform Team: platform@pea.co.th
- On-call: +66-XXX-XXX-XXXX

## Checklist

### Pre-deployment
- [ ] All tests passing (214/214)
- [ ] Security scan clean
- [ ] Load test passed (P95 < 500ms)
- [ ] Database backup taken
- [ ] Rollback plan documented

### Post-deployment
- [ ] Health check passing
- [ ] Metrics flowing to Grafana
- [ ] Alerts configured
- [ ] SSL certificate valid
- [ ] Stakeholders notified

---

**Version**: 1.0.0
**Last Updated**: December 2024
