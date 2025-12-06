# PEA RE Forecast Platform - Deployment Runbook

**Version**: 1.0.0
**Last Updated**: December 6, 2024
**Owner**: PEA Development Team
**TOR Compliance**: Sections 7.1.4, 7.1.5, 7.1.6

---

## Table of Contents

1. [Overview](#overview)
2. [Pre-Deployment Checklist](#pre-deployment-checklist)
3. [Staging Deployment](#staging-deployment)
4. [Production Deployment](#production-deployment)
5. [Database Migrations](#database-migrations)
6. [Rollback Procedures](#rollback-procedures)
7. [Post-Deployment Verification](#post-deployment-verification)
8. [Monitoring and Alerting](#monitoring-and-alerting)
9. [Troubleshooting](#troubleshooting)
10. [Emergency Contacts](#emergency-contacts)

---

## Overview

### System Components

The PEA RE Forecast Platform consists of:

- **Backend API** (FastAPI): Solar forecasting and voltage prediction services
- **Frontend Dashboard** (Next.js): User interface for operators
- **TimescaleDB**: Time-series database for measurements and predictions
- **Redis**: Caching layer for prediction results
- **ML Models**: XGBoost models for solar and voltage predictions

### Deployment Strategy

- **Staging**: Rolling update with 1 replica buffer
- **Production**: Blue-green deployment with health check validation
- **Rollback Window**: 15 minutes post-deployment

### Infrastructure

Per TOR Section 7.1.1:
- **Web Server**: 4 Core, 6 GB RAM
- **AI/ML Server**: 16 Core, 64 GB RAM
- **Database Server**: 8 Core, 32 GB RAM
- **OS**: Ubuntu Server 22.04 LTS
- **Orchestration**: Kubernetes 1.28+

---

## Pre-Deployment Checklist

### 1. Code Quality and Testing

Execute all verification steps before proceeding:

```bash
# Navigate to project root
cd /Users/fero/Desktop/PEA/pea-re-forecast-platform

# Run full test suite (must pass all 555 tests)
./scripts/run-tests.sh

# Expected output:
# Backend: 555 passed
# Frontend: All tests passed
# Integration: All scenarios passed
```

**Pass Criteria**:
- [ ] All 555 backend tests passing
- [ ] All frontend unit tests passing
- [ ] Integration tests passing
- [ ] No critical bugs in issue tracker

### 2. Security Scanning

```bash
# Container image scanning (TOR 7.1.6 - Security Requirements)
trivy image pea-forecast/backend:${VERSION}
trivy image pea-forecast/frontend:${VERSION}

# Pass criteria: No CRITICAL or HIGH vulnerabilities
```

```bash
# Code quality scanning
sonarqube-scanner \
  -Dsonar.projectKey=pea-re-forecast \
  -Dsonar.sources=backend/app,frontend/src

# Pass criteria:
# - Quality Gate: PASSED
# - Security Hotspots: 0
# - Code Coverage: >80%
```

```bash
# License compliance (TOR 7.1.5 - Software Licensing)
black-duck-scan --project pea-re-forecast --version ${VERSION}

# Pass criteria: All licenses approved for production use
```

### 3. Model Performance Validation

**TOR Compliance Check** (Section 7.1 - System Requirements):

```bash
# Validate ML model accuracy against TOR requirements
python ml/scripts/validate_models.py

# Expected metrics:
# Solar Forecast Model:
#   - MAPE: < 10% (TOR requirement)
#   - RMSE: < 100 kW (TOR requirement)
#   - R²: > 0.95 (TOR requirement)
#
# Voltage Prediction Model:
#   - MAE: < 2V (TOR requirement)
#   - RMSE: < 3V
#   - R²: > 0.90
```

**Pass Criteria**:
- [ ] Solar MAPE < 10%
- [ ] Solar RMSE < 100 kW
- [ ] Solar R² > 0.95
- [ ] Voltage MAE < 2V

### 4. Performance Testing

```bash
# Load test API endpoints
k6 run scripts/load-tests/api-load-test.js

# Pass criteria:
# - Avg response time: < 500ms (TOR requirement)
# - p95 response time: < 1000ms
# - Error rate: < 0.1%
# - Concurrent users: 1000+ (scales to 300,000 consumers per TOR 7.1.7)
```

### 5. Environment Configuration

```bash
# Verify environment variables are set
kubectl get secret timescaledb-credentials -n pea-forecast-prod
kubectl get secret keycloak-secrets -n pea-forecast-prod
kubectl get configmap backend-config -n pea-forecast-prod

# Expected: All secrets and configmaps exist
```

### 6. Database Backup

```bash
# Create pre-deployment backup (CRITICAL)
kubectl exec -n pea-forecast-prod timescaledb-0 -- \
  pg_dump -U postgres pea_forecast > \
  /backups/pea_forecast_$(date +%Y%m%d_%H%M%S).sql

# Verify backup size (should be >0 bytes)
ls -lh /backups/pea_forecast_*.sql | tail -1
```

### 7. Helm Chart Validation

```bash
# Lint Helm chart
helm lint infrastructure/helm/pea-re-forecast

# Dry-run deployment
helm upgrade --install pea-re-forecast \
  infrastructure/helm/pea-re-forecast \
  -f infrastructure/helm/pea-re-forecast/values-prod.yaml \
  --namespace pea-forecast-prod \
  --dry-run --debug

# Expected: No errors, valid manifests
```

### Pre-Deployment Sign-Off

**Required Approvals**:
- [ ] Technical Lead: Code review complete
- [ ] QA Team: All tests passing
- [ ] Security Team: Security scans approved
- [ ] DevOps Team: Infrastructure ready
- [ ] PEA System Administrator: Deployment window confirmed

---

## Staging Deployment

### 1. Build and Push Images

```bash
# Set version tag
export VERSION="v1.0.0"
export REGISTRY="registry.gitlab.pea.co.th/re-forecast"

# Build backend image
docker build -t ${REGISTRY}/backend:${VERSION} \
  -f backend/Dockerfile \
  backend/

# Build frontend image
docker build -t ${REGISTRY}/frontend:${VERSION} \
  -f frontend/Dockerfile \
  frontend/

# Push to GitLab Container Registry (TOR: GitLab Registry)
docker push ${REGISTRY}/backend:${VERSION}
docker push ${REGISTRY}/frontend:${VERSION}

# Tag as staging
docker tag ${REGISTRY}/backend:${VERSION} ${REGISTRY}/backend:staging
docker tag ${REGISTRY}/frontend:${VERSION} ${REGISTRY}/frontend:staging
docker push ${REGISTRY}/backend:staging
docker push ${REGISTRY}/frontend:staging
```

### 2. Deploy to Staging

```bash
# Deploy using Helm
helm upgrade --install pea-re-forecast \
  infrastructure/helm/pea-re-forecast \
  -f infrastructure/helm/pea-re-forecast/values-staging.yaml \
  --set backend.image.tag=staging \
  --set frontend.image.tag=staging \
  --namespace pea-forecast-staging \
  --create-namespace \
  --wait \
  --timeout 10m

# Expected output:
# Release "pea-re-forecast" has been upgraded. Happy Helming!
# NAME: pea-re-forecast
# STATUS: deployed
```

### 3. Verify Staging Deployment

```bash
# Check pod status
kubectl get pods -n pea-forecast-staging

# Expected: All pods Running with 2/2 or 1/1 READY
# NAME                          READY   STATUS    RESTARTS   AGE
# backend-xxxxxxxxx-xxxxx       1/1     Running   0          2m
# backend-xxxxxxxxx-xxxxx       1/1     Running   0          2m
# frontend-xxxxxxxxx-xxxxx      1/1     Running   0          2m
# frontend-xxxxxxxxx-xxxxx      1/1     Running   0          2m
# timescaledb-0                 1/1     Running   0          2m
# redis-0                       1/1     Running   0          2m
```

```bash
# Check service endpoints
kubectl get svc -n pea-forecast-staging

# Expected: All services have ClusterIP assigned
```

### 4. Smoke Tests (Staging)

```bash
# Port-forward to backend
kubectl port-forward -n pea-forecast-staging svc/backend 8000:8000 &

# Health check
curl http://localhost:8000/api/v1/health

# Expected: {"status":"healthy","version":"v1.0.0"}
```

```bash
# Test solar forecast endpoint
curl -X POST http://localhost:8000/api/v1/forecast/solar \
  -H "Content-Type: application/json" \
  -d '{
    "timestamp": "2024-12-06T12:00:00+07:00",
    "horizon_minutes": 60,
    "features": {
      "pyrano1": 850.5,
      "pyrano2": 842.3,
      "pvtemp1": 45.2,
      "pvtemp2": 44.8,
      "ambtemp": 32.5,
      "windspeed": 2.3
    }
  }'

# Expected: JSON response with prediction
# {
#   "status": "success",
#   "data": {
#     "prediction": {...},
#     "model_version": "solar-xgb-v1.0.0"
#   }
# }
```

```bash
# Test voltage prediction endpoint
curl -X POST http://localhost:8000/api/v1/forecast/voltage \
  -H "Content-Type: application/json" \
  -d '{
    "timestamp": "2024-12-06T12:00:00+07:00",
    "prosumer_ids": ["prosumer1", "prosumer2"]
  }'

# Expected: JSON response with voltage predictions
```

```bash
# Test frontend
kubectl port-forward -n pea-forecast-staging svc/frontend 3000:3000 &

# Open browser to http://localhost:3000
# Verify:
# - Dashboard loads
# - Charts render
# - Real-time updates work
```

### 5. Performance Validation (Staging)

```bash
# Measure response time (must be < 500ms per TOR)
time curl -s http://localhost:8000/api/v1/forecast/solar \
  -X POST \
  -H "Content-Type: application/json" \
  -d @test-data/solar-request.json

# Expected: real time < 0.5s
```

### Staging Sign-Off

- [ ] All pods healthy and running
- [ ] Health endpoints responding
- [ ] Solar forecast API working (response < 500ms)
- [ ] Voltage prediction API working (response < 500ms)
- [ ] Frontend dashboard accessible
- [ ] No errors in logs

**Proceed to Production**: Yes / No

---

## Production Deployment

### Deployment Window

**Recommended Schedule**:
- **Day**: Tuesday or Wednesday (avoid Friday)
- **Time**: 02:00 - 04:00 ICT (low traffic period)
- **Duration**: 2 hours (deployment + verification)

### Communication Plan

**T-24 hours**: Send deployment notification to:
- PEA Operations Team
- Grid Operators
- System Administrators
- Stakeholders

**Email Template**:
```
Subject: [SCHEDULED] PEA RE Forecast Platform Deployment - v1.0.0

Dear Team,

Scheduled deployment of PEA RE Forecast Platform version v1.0.0

Date: [Date]
Time: 02:00 - 04:00 ICT
Duration: ~2 hours
Expected Downtime: < 5 minutes (rolling update)

Changes:
- [List major features/fixes]

Rollback Plan: Available if issues detected within 15 minutes

Contact: [Emergency contact details]
```

### 1. Pre-Production Checklist

```bash
# Verify production namespace exists
kubectl get namespace pea-forecast-prod

# If not exists:
kubectl create namespace pea-forecast-prod
```

```bash
# Create/update production secrets
kubectl create secret generic timescaledb-credentials \
  --from-literal=username=postgres \
  --from-literal=password=${TIMESCALEDB_PASSWORD} \
  --namespace=pea-forecast-prod \
  --dry-run=client -o yaml | kubectl apply -f -

kubectl create secret generic keycloak-secrets \
  --from-literal=client-id=pea-forecast-api \
  --from-literal=client-secret=${KEYCLOAK_CLIENT_SECRET} \
  --namespace=pea-forecast-prod \
  --dry-run=client -o yaml | kubectl apply -f -
```

```bash
# Verify Longhorn storage class (TOR: Longhorn storage)
kubectl get storageclass longhorn

# Expected: longhorn storage class exists
```

### 2. Database Migration (if required)

```bash
# Check for pending migrations
kubectl exec -n pea-forecast-prod timescaledb-0 -- \
  psql -U postgres -d pea_forecast -c \
  "SELECT version, dirty FROM schema_migrations ORDER BY version DESC LIMIT 1;"

# If migrations pending:
# 1. Backup database (already done in pre-deployment)
# 2. Run migrations

# Apply migrations using Alembic
kubectl exec -n pea-forecast-prod deployment/backend -- \
  alembic upgrade head

# Verify migrations applied
kubectl exec -n pea-forecast-prod timescaledb-0 -- \
  psql -U postgres -d pea_forecast -c \
  "SELECT version, dirty FROM schema_migrations ORDER BY version DESC LIMIT 1;"

# Expected: Latest version, dirty = false
```

### 3. Deploy to Production

```bash
# Tag images as production
docker tag ${REGISTRY}/backend:${VERSION} ${REGISTRY}/backend:prod
docker tag ${REGISTRY}/frontend:${VERSION} ${REGISTRY}/frontend:prod
docker push ${REGISTRY}/backend:prod
docker push ${REGISTRY}/frontend:prod

# Deploy using Helm with production values
helm upgrade --install pea-re-forecast \
  infrastructure/helm/pea-re-forecast \
  -f infrastructure/helm/pea-re-forecast/values-prod.yaml \
  --set backend.image.tag=prod \
  --set frontend.image.tag=prod \
  --namespace pea-forecast-prod \
  --wait \
  --timeout 15m \
  --atomic

# --atomic flag: Rollback automatically if deployment fails
```

**Deployment Progress Monitoring**:

```bash
# Watch rollout status
kubectl rollout status deployment/backend -n pea-forecast-prod
kubectl rollout status deployment/frontend -n pea-forecast-prod

# Expected:
# deployment "backend" successfully rolled out
# deployment "frontend" successfully rolled out
```

```bash
# Monitor pod status in real-time
watch -n 2 'kubectl get pods -n pea-forecast-prod'

# Wait until all pods show Running with READY 1/1 or 2/2
```

### 4. Post-Deployment Verification (Production)

#### Health Checks

```bash
# Backend health check
kubectl exec -n pea-forecast-prod deployment/backend -- \
  curl -f http://localhost:8000/api/v1/health

# Expected: {"status":"healthy","version":"v1.0.0"}
```

```bash
# Frontend health check
kubectl exec -n pea-forecast-prod deployment/frontend -- \
  curl -f http://localhost:3000/api/health

# Expected: 200 OK
```

#### TOR Compliance Verification

**Solar Forecast Accuracy** (TOR Requirement: MAPE < 10%):

```bash
# Run accuracy validation against production data
kubectl exec -n pea-forecast-prod deployment/backend -- \
  python -m app.cli validate-model --model solar --last-days 7

# Expected:
# Solar Model Validation Results:
# MAPE: 7.2% ✓ (< 10%)
# RMSE: 85.3 kW ✓ (< 100 kW)
# R²: 0.963 ✓ (> 0.95)
```

**Voltage Prediction Accuracy** (TOR Requirement: MAE < 2V):

```bash
# Run voltage model validation
kubectl exec -n pea-forecast-prod deployment/backend -- \
  python -m app.cli validate-model --model voltage --last-days 7

# Expected:
# Voltage Model Validation Results:
# MAE: 1.4V ✓ (< 2V)
# RMSE: 2.1V
# R²: 0.92
```

**API Performance** (TOR Requirement: Response time < 500ms):

```bash
# Test API latency
for i in {1..10}; do
  kubectl exec -n pea-forecast-prod deployment/backend -- \
    time curl -s http://localhost:8000/api/v1/forecast/solar \
    -X POST \
    -H "Content-Type: application/json" \
    -d @/app/test-data/solar-request.json
done | grep real | awk '{print $2}'

# Expected: All requests < 0.5s (500ms)
```

#### Functional Testing

```bash
# Test solar forecast API
kubectl port-forward -n pea-forecast-prod svc/backend 8000:8000 &

curl -X POST http://localhost:8000/api/v1/forecast/solar \
  -H "Authorization: Bearer ${ACCESS_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "timestamp": "2024-12-06T14:00:00+07:00",
    "horizon_minutes": 60,
    "features": {
      "pyrano1": 920.0,
      "pyrano2": 915.5,
      "pvtemp1": 48.5,
      "pvtemp2": 47.9,
      "ambtemp": 34.2,
      "windspeed": 1.8
    }
  }'

# Expected: Valid prediction response
```

```bash
# Test voltage prediction API
curl -X POST http://localhost:8000/api/v1/forecast/voltage \
  -H "Authorization: Bearer ${ACCESS_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "timestamp": "2024-12-06T14:00:00+07:00",
    "prosumer_ids": ["prosumer1", "prosumer5", "prosumer7"]
  }'

# Expected: Voltage predictions for all requested prosumers
```

```bash
# Test alert system
curl http://localhost:8000/api/v1/alerts?status=active \
  -H "Authorization: Bearer ${ACCESS_TOKEN}"

# Expected: List of active alerts (may be empty)
```

#### Database Verification

```bash
# Check database connectivity
kubectl exec -n pea-forecast-prod timescaledb-0 -- \
  psql -U postgres -d pea_forecast -c "SELECT version();"

# Verify data ingestion
kubectl exec -n pea-forecast-prod timescaledb-0 -- \
  psql -U postgres -d pea_forecast -c \
  "SELECT COUNT(*), MAX(time) FROM solar_measurements;"

# Expected: Recent data (within last hour)
```

```bash
# Verify predictions being stored
kubectl exec -n pea-forecast-prod timescaledb-0 -- \
  psql -U postgres -d pea_forecast -c \
  "SELECT model_type, COUNT(*), MAX(time) FROM predictions GROUP BY model_type;"

# Expected:
#  model_type | count | max
# ------------+-------+------------------------
#  solar      | XXXXX | 2024-12-06 14:00:00+07
#  voltage    | XXXXX | 2024-12-06 14:00:00+07
```

#### Redis Cache Verification

```bash
# Check Redis connectivity
kubectl exec -n pea-forecast-prod redis-0 -- redis-cli PING

# Expected: PONG
```

```bash
# Verify cache hit rate
kubectl exec -n pea-forecast-prod redis-0 -- \
  redis-cli INFO stats | grep keyspace_hits

# Expected: keyspace_hits should increase over time
```

#### Audit Log Verification (TOR 7.1.6)

```bash
# Verify audit logging is active
kubectl exec -n pea-forecast-prod timescaledb-0 -- \
  psql -U postgres -d pea_forecast -c \
  "SELECT COUNT(*), MAX(time) FROM audit_log WHERE time > NOW() - INTERVAL '1 hour';"

# Expected: Recent audit entries
```

### 5. Load Testing (Production)

**CAUTION**: Run during deployment window only.

```bash
# Gradual load ramp-up
k6 run --vus 100 --duration 5m scripts/load-tests/production-load-test.js

# Monitor metrics during load test:
# - Response time (must stay < 500ms)
# - Error rate (must stay < 0.1%)
# - CPU utilization (should trigger HPA if > 60%)
# - Memory utilization (should stay < 70%)
```

```bash
# Verify HPA scaling (if enabled)
kubectl get hpa -n pea-forecast-prod

# Expected: Replicas scale up during high load
```

### 6. Monitoring Dashboard Verification

Access Grafana dashboards:

```bash
# Port-forward to Grafana
kubectl port-forward -n monitoring svc/grafana 3001:80 &

# Open: http://localhost:3001
# Credentials: admin / <grafana-password>
```

**Dashboards to verify**:
- [ ] PEA RE Forecast - Overview
- [ ] API Performance Metrics
- [ ] Model Accuracy Metrics
- [ ] Database Performance
- [ ] Kubernetes Resources

**Key Metrics** (first 30 minutes):
- Request rate: Should match expected traffic
- Error rate: < 0.1%
- Avg response time: < 500ms
- p95 response time: < 1000ms
- CPU usage: < 70%
- Memory usage: < 70%

### Production Sign-Off

**Verification Checklist**:
- [ ] All pods healthy (3/3 backend, 3/3 frontend)
- [ ] Health endpoints responding
- [ ] TOR accuracy requirements met (MAPE < 10%, MAE < 2V)
- [ ] API performance < 500ms
- [ ] Database migrations successful
- [ ] Audit logging active (TOR 7.1.6)
- [ ] No critical errors in logs
- [ ] Monitoring dashboards showing healthy metrics
- [ ] Cache layer functioning
- [ ] Frontend accessible via production URL

**Approvals**:
- [ ] Technical Lead
- [ ] PEA System Administrator
- [ ] Operations Team Lead

---

## Database Migrations

### Migration Strategy

Database migrations are managed using Alembic for schema changes.

### Pre-Migration Backup

```bash
# CRITICAL: Always backup before migrations
kubectl exec -n pea-forecast-prod timescaledb-0 -- \
  pg_dump -U postgres -Fc pea_forecast > \
  /backups/pea_forecast_pre_migration_$(date +%Y%m%d_%H%M%S).dump

# Verify backup
ls -lh /backups/pea_forecast_pre_migration_*.dump | tail -1
```

### Running Migrations

```bash
# Check current migration version
kubectl exec -n pea-forecast-prod deployment/backend -- \
  alembic current

# Check pending migrations
kubectl exec -n pea-forecast-prod deployment/backend -- \
  alembic history

# Apply migrations
kubectl exec -n pea-forecast-prod deployment/backend -- \
  alembic upgrade head

# Verify successful migration
kubectl exec -n pea-forecast-prod deployment/backend -- \
  alembic current

# Expected: Shows latest migration version
```

### Migration Rollback

```bash
# Rollback to previous version
kubectl exec -n pea-forecast-prod deployment/backend -- \
  alembic downgrade -1

# Or rollback to specific version
kubectl exec -n pea-forecast-prod deployment/backend -- \
  alembic downgrade <revision_id>
```

### Data Migration

For large data migrations (>1M rows):

```bash
# Run data migration script in background
kubectl exec -n pea-forecast-prod timescaledb-0 -- \
  psql -U postgres -d pea_forecast -f /migrations/data_migration_v1.0.0.sql &

# Monitor progress
kubectl exec -n pea-forecast-prod timescaledb-0 -- \
  psql -U postgres -d pea_forecast -c \
  "SELECT * FROM migration_status WHERE version = 'v1.0.0';"
```

---

## Rollback Procedures

### Rollback Decision Criteria

Initiate rollback if:
- Error rate > 1%
- Response time > 2000ms (4x TOR requirement)
- Critical functionality broken (solar/voltage predictions failing)
- Database corruption detected
- Security vulnerability discovered

### Helm Rollback

```bash
# View deployment history
helm history pea-re-forecast -n pea-forecast-prod

# Example output:
# REVISION  UPDATED                   STATUS      CHART                 DESCRIPTION
# 1         Mon Dec 4 02:00:00 2024   superseded  pea-re-forecast-0.1.0 Install complete
# 2         Wed Dec 6 02:15:00 2024   deployed    pea-re-forecast-0.1.0 Upgrade complete

# Rollback to previous revision
helm rollback pea-re-forecast 1 -n pea-forecast-prod --wait

# Expected: Deployment rolls back to previous version
```

### Manual Rollback (if Helm fails)

```bash
# Rollback backend deployment
kubectl set image deployment/backend \
  backend=${REGISTRY}/backend:v0.9.0 \
  -n pea-forecast-prod

# Rollback frontend deployment
kubectl set image deployment/frontend \
  frontend=${REGISTRY}/frontend:v0.9.0 \
  -n pea-forecast-prod

# Monitor rollback
kubectl rollout status deployment/backend -n pea-forecast-prod
kubectl rollout status deployment/frontend -n pea-forecast-prod
```

### Database Rollback

```bash
# CRITICAL: Only if database migration caused issues

# Stop application pods (prevent writes)
kubectl scale deployment/backend --replicas=0 -n pea-forecast-prod

# Restore from backup
kubectl exec -n pea-forecast-prod timescaledb-0 -- \
  pg_restore -U postgres -d pea_forecast -c \
  /backups/pea_forecast_pre_migration_YYYYMMDD_HHMMSS.dump

# Verify restoration
kubectl exec -n pea-forecast-prod timescaledb-0 -- \
  psql -U postgres -d pea_forecast -c \
  "SELECT COUNT(*) FROM solar_measurements;"

# Restart application
kubectl scale deployment/backend --replicas=3 -n pea-forecast-prod
```

### Rollback Verification

```bash
# Verify pods running previous version
kubectl get pods -n pea-forecast-prod -o wide

# Check health endpoints
kubectl exec -n pea-forecast-prod deployment/backend -- \
  curl http://localhost:8000/api/v1/health

# Verify version
# Expected: {"status":"healthy","version":"v0.9.0"}
```

### Post-Rollback Communication

```
Subject: [COMPLETED] PEA RE Forecast Platform Rollback - v1.0.0

Dear Team,

Deployment of v1.0.0 has been rolled back to v0.9.0 due to [reason].

Rollback completed: [timestamp]
Current version: v0.9.0
Status: Stable

Issue identified: [description]
Next steps: [action plan]

Contact: [emergency contact]
```

---

## Post-Deployment Verification

### 24-Hour Monitoring Plan

**First Hour**:
- [ ] Watch for errors in logs every 10 minutes
- [ ] Monitor API response times
- [ ] Check prediction accuracy
- [ ] Verify no alert storms

**First 4 Hours**:
- [ ] Review Grafana dashboards every 30 minutes
- [ ] Check error rates in Prometheus
- [ ] Verify data ingestion rate
- [ ] Monitor database performance

**First 24 Hours**:
- [ ] Review daily summary metrics
- [ ] Analyze user feedback
- [ ] Check audit logs for anomalies
- [ ] Verify backup jobs completed

### Key Metrics to Monitor

#### API Performance

```bash
# Query Prometheus for API metrics
kubectl port-forward -n monitoring svc/prometheus 9090:9090 &

# Open: http://localhost:9090
# Query: rate(http_request_duration_seconds_sum[5m]) / rate(http_request_duration_seconds_count[5m])
# Expected: < 0.5 seconds
```

#### Model Accuracy

```bash
# Daily accuracy report
kubectl exec -n pea-forecast-prod deployment/backend -- \
  python -m app.cli daily-accuracy-report

# Expected:
# Solar MAPE: < 10%
# Voltage MAE: < 2V
```

#### Error Rates

```bash
# Check application logs for errors
kubectl logs -n pea-forecast-prod deployment/backend --tail=100 | grep ERROR

# Expected: No critical errors
```

#### Resource Utilization

```bash
# Check resource usage
kubectl top pods -n pea-forecast-prod

# Expected:
# - CPU: < 70% of limits
# - Memory: < 70% of limits
```

### Verification Commands

```bash
# Health check script (run every hour for first 24 hours)
cat << 'EOF' > /tmp/health-check.sh
#!/bin/bash
echo "=== Health Check $(date) ==="

echo "1. Pod Status:"
kubectl get pods -n pea-forecast-prod

echo "2. Backend Health:"
kubectl exec -n pea-forecast-prod deployment/backend -- \
  curl -s http://localhost:8000/api/v1/health | jq .

echo "3. Recent Errors:"
kubectl logs -n pea-forecast-prod deployment/backend --tail=50 | grep -i error | tail -5

echo "4. API Response Time (sample):"
time kubectl exec -n pea-forecast-prod deployment/backend -- \
  curl -s http://localhost:8000/api/v1/forecast/solar \
  -X POST -H "Content-Type: application/json" \
  -d '{"timestamp":"'$(date -Iseconds)'","horizon_minutes":60,"features":{"pyrano1":850,"pyrano2":845,"pvtemp1":45,"pvtemp2":44,"ambtemp":32,"windspeed":2}}'

echo "5. Database Status:"
kubectl exec -n pea-forecast-prod timescaledb-0 -- \
  psql -U postgres -d pea_forecast -c "SELECT COUNT(*) as recent_measurements FROM solar_measurements WHERE time > NOW() - INTERVAL '1 hour';"

echo "=== End Health Check ==="
EOF

chmod +x /tmp/health-check.sh
/tmp/health-check.sh
```

---

## Monitoring and Alerting

### Prometheus Alerts

Key alerts configured for the platform:

```yaml
# Alert: High API Error Rate
alert: HighAPIErrorRate
expr: rate(http_requests_total{status=~"5.."}[5m]) > 0.01
for: 5m
severity: critical
description: API error rate exceeds 1%

# Alert: Slow API Response
alert: SlowAPIResponse
expr: http_request_duration_seconds{quantile="0.95"} > 1.0
for: 10m
severity: warning
description: API p95 response time exceeds 1 second (TOR requirement: <500ms)

# Alert: Model Accuracy Degradation
alert: ModelAccuracyDegraded
expr: model_mape > 10
for: 1h
severity: critical
description: Solar model MAPE exceeds TOR requirement of 10%

# Alert: Pod CrashLoop
alert: PodCrashLooping
expr: rate(kube_pod_container_status_restarts_total[15m]) > 0
for: 5m
severity: critical
description: Pod is crash looping

# Alert: Database Connection Pool Exhausted
alert: DBConnectionPoolExhausted
expr: db_connection_pool_available < 5
for: 5m
severity: critical
description: Database connection pool nearly exhausted
```

### Grafana Dashboards

Access dashboards at: `http://grafana.pea-forecast.go.th`

**PEA RE Forecast - Overview**:
- Request rate
- Error rate
- Response time (p50, p95, p99)
- Active users
- Prediction count

**Model Performance**:
- Solar MAPE (target: <10%)
- Voltage MAE (target: <2V)
- Prediction latency
- Model versions deployed

**Infrastructure**:
- CPU utilization
- Memory utilization
- Disk I/O
- Network traffic

### Log Aggregation

```bash
# Query logs using kubectl
kubectl logs -n pea-forecast-prod deployment/backend --tail=100 -f

# Filter for errors
kubectl logs -n pea-forecast-prod deployment/backend --tail=1000 | grep ERROR

# Filter for specific request ID
kubectl logs -n pea-forecast-prod deployment/backend --tail=10000 | grep "request_id=abc-123"
```

**Opensearch** (TOR: Opensearch for observability):

```bash
# Port-forward to Opensearch Dashboards
kubectl port-forward -n monitoring svc/opensearch-dashboards 5601:5601 &

# Open: http://localhost:5601
# Query: level:ERROR AND service:pea-forecast
```

### Audit Logs (TOR 7.1.6)

```bash
# View recent audit logs
kubectl exec -n pea-forecast-prod timescaledb-0 -- \
  psql -U postgres -d pea_forecast -c \
  "SELECT time, user_email, action, resource_type, response_status
   FROM audit_log
   WHERE time > NOW() - INTERVAL '1 hour'
   ORDER BY time DESC
   LIMIT 50;"

# Check for failed authentication attempts
kubectl exec -n pea-forecast-prod timescaledb-0 -- \
  psql -U postgres -d pea_forecast -c \
  "SELECT time, user_email, user_ip, response_status
   FROM audit_log
   WHERE action = 'login' AND response_status >= 400
   AND time > NOW() - INTERVAL '24 hours';"
```

---

## Troubleshooting

### Common Issues

#### Issue 1: Pods Not Starting

**Symptoms**:
```bash
kubectl get pods -n pea-forecast-prod
# NAME                       READY   STATUS             RESTARTS   AGE
# backend-xxx                0/1     CrashLoopBackOff   5          5m
```

**Diagnosis**:
```bash
# Check pod events
kubectl describe pod backend-xxx -n pea-forecast-prod

# Check logs
kubectl logs backend-xxx -n pea-forecast-prod
```

**Common Causes**:
1. **Database connection failed**
   - Verify TimescaleDB is running
   - Check credentials in secret
   ```bash
   kubectl get secret timescaledb-credentials -n pea-forecast-prod -o yaml
   ```

2. **Missing environment variables**
   - Verify configmap exists
   ```bash
   kubectl get configmap backend-config -n pea-forecast-prod
   ```

3. **Image pull error**
   - Verify image exists in registry
   ```bash
   docker pull ${REGISTRY}/backend:prod
   ```

**Resolution**:
```bash
# Fix and restart
kubectl rollout restart deployment/backend -n pea-forecast-prod
```

#### Issue 2: High API Latency (>500ms)

**Symptoms**:
- API response time exceeds TOR requirement of 500ms

**Diagnosis**:
```bash
# Check current response times
kubectl exec -n pea-forecast-prod deployment/backend -- \
  curl -w "\nTime: %{time_total}s\n" \
  -s http://localhost:8000/api/v1/health

# Check Redis cache
kubectl exec -n pea-forecast-prod redis-0 -- \
  redis-cli INFO stats | grep keyspace_hits
```

**Common Causes**:
1. **Cache miss rate high**
   - Redis not working
   - Cache TTL too short

2. **Database slow queries**
   ```bash
   kubectl exec -n pea-forecast-prod timescaledb-0 -- \
     psql -U postgres -d pea_forecast -c \
     "SELECT query, mean_exec_time FROM pg_stat_statements ORDER BY mean_exec_time DESC LIMIT 10;"
   ```

3. **Model inference slow**
   - Check ML server CPU utilization
   ```bash
   kubectl top pods -n pea-forecast-prod
   ```

**Resolution**:
```bash
# Scale up backend replicas
kubectl scale deployment/backend --replicas=5 -n pea-forecast-prod

# Verify cache working
kubectl logs -n pea-forecast-prod deployment/backend | grep "cache_hit"

# Optimize database (if needed)
kubectl exec -n pea-forecast-prod timescaledb-0 -- \
  psql -U postgres -d pea_forecast -c "VACUUM ANALYZE;"
```

#### Issue 3: Model Accuracy Degradation

**Symptoms**:
- Solar MAPE > 10% (exceeds TOR requirement)
- Voltage MAE > 2V (exceeds TOR requirement)

**Diagnosis**:
```bash
# Check model version
kubectl exec -n pea-forecast-prod deployment/backend -- \
  python -m app.cli model-info

# Validate current accuracy
kubectl exec -n pea-forecast-prod deployment/backend -- \
  python -m app.cli validate-model --model solar --last-days 7
```

**Common Causes**:
1. **Data drift** - Input data distribution changed
2. **Sensor failure** - Missing or corrupt sensor data
3. **Model version mismatch** - Wrong model loaded

**Resolution**:
```bash
# Trigger model retraining
kubectl exec -n pea-forecast-prod deployment/backend -- \
  python -m app.cli trigger-retraining --model solar

# Or rollback to previous model version
kubectl exec -n pea-forecast-prod deployment/backend -- \
  python -m app.cli load-model --model solar --version v0.9.0
```

#### Issue 4: Database Connection Pool Exhausted

**Symptoms**:
```
ERROR: Database connection pool exhausted
ERROR: could not obtain connection from pool
```

**Diagnosis**:
```bash
# Check active connections
kubectl exec -n pea-forecast-prod timescaledb-0 -- \
  psql -U postgres -d pea_forecast -c \
  "SELECT count(*) FROM pg_stat_activity WHERE state = 'active';"

# Check max connections
kubectl exec -n pea-forecast-prod timescaledb-0 -- \
  psql -U postgres -d pea_forecast -c "SHOW max_connections;"
```

**Resolution**:
```bash
# Increase connection pool size (edit values-prod.yaml)
# backend.env.DB_POOL_SIZE: "20"

# Restart backend
kubectl rollout restart deployment/backend -n pea-forecast-prod

# Or increase max_connections in PostgreSQL
kubectl exec -n pea-forecast-prod timescaledb-0 -- \
  psql -U postgres -c "ALTER SYSTEM SET max_connections = 200;"

# Restart database
kubectl rollout restart statefulset/timescaledb -n pea-forecast-prod
```

#### Issue 5: Frontend 502 Bad Gateway

**Symptoms**:
- Frontend returns 502 error
- Cannot access dashboard

**Diagnosis**:
```bash
# Check backend service
kubectl get svc backend -n pea-forecast-prod

# Check backend pods
kubectl get pods -l app=backend -n pea-forecast-prod

# Check ingress
kubectl get ingress -n pea-forecast-prod
kubectl describe ingress pea-re-forecast -n pea-forecast-prod
```

**Resolution**:
```bash
# Verify backend is responding
kubectl exec -n pea-forecast-prod deployment/frontend -- \
  curl http://backend:8000/api/v1/health

# Restart frontend
kubectl rollout restart deployment/frontend -n pea-forecast-prod

# Check Kong gateway logs (if using Kong)
kubectl logs -n pea-forecast-prod -l app=kong
```

### Log Locations

```bash
# Application logs
kubectl logs -n pea-forecast-prod deployment/backend -c backend
kubectl logs -n pea-forecast-prod deployment/frontend -c frontend

# Database logs
kubectl logs -n pea-forecast-prod timescaledb-0

# Redis logs
kubectl logs -n pea-forecast-prod redis-0

# Ingress logs
kubectl logs -n pea-forecast-prod -l app=kong

# Kubernetes events
kubectl get events -n pea-forecast-prod --sort-by='.lastTimestamp'
```

### Debug Mode

To enable debug logging temporarily:

```bash
# Enable debug logging for backend
kubectl set env deployment/backend LOG_LEVEL=DEBUG -n pea-forecast-prod

# View debug logs
kubectl logs -n pea-forecast-prod deployment/backend -f

# Revert to INFO level
kubectl set env deployment/backend LOG_LEVEL=INFO -n pea-forecast-prod
```

---

## Emergency Contacts

### Escalation Path

**Level 1** - Development Team (Response: 15 minutes)
- On-Call DevOps Engineer: [Phone]
- Backend Lead: [Phone]
- Frontend Lead: [Phone]

**Level 2** - Technical Leadership (Response: 30 minutes)
- Technical Architect: [Phone]
- Engineering Manager: [Phone]

**Level 3** - PEA Management (Response: 1 hour)
- PEA System Administrator: [Phone]
- PEA IT Director: [Phone]

### Support Channels

- **Slack**: #pea-forecast-ops (real-time)
- **Email**: pea-forecast-support@pea.co.th
- **Issue Tracker**: https://gitlab.pea.co.th/re-forecast/pea-re-forecast/issues
- **On-Call**: PagerDuty (TBD)

### Vendor Support

- **Kubernetes**: Internal support team
- **TimescaleDB**: support@timescale.com (if enterprise license)
- **Kong Gateway**: support.konghq.com (if enterprise)

---

## Appendix

### A. Deployment Checklist (Printable)

```
PRE-DEPLOYMENT
□ All 555 tests passing
□ Security scans completed (Trivy, SonarQube, Black Duck)
□ Model accuracy validated (MAPE < 10%, MAE < 2V)
□ Performance tests passed (latency < 500ms)
□ Database backup created
□ Helm chart validated (lint + dry-run)
□ Deployment notification sent (T-24h)
□ All approvals obtained

STAGING DEPLOYMENT
□ Images built and pushed to registry
□ Helm deployment successful
□ All pods running and healthy
□ Health endpoints responding
□ API smoke tests passed
□ Frontend accessible
□ No errors in logs

PRODUCTION DEPLOYMENT
□ Production secrets verified
□ Database migrations applied (if needed)
□ Helm deployment successful (--atomic)
□ All pods running (3/3 replicas)
□ Health checks passing
□ TOR compliance verified (MAPE, MAE, latency)
□ Audit logging active
□ Monitoring dashboards updated
□ Load testing completed
□ No critical errors

POST-DEPLOYMENT
□ 1-hour monitoring completed
□ 4-hour monitoring completed
□ 24-hour monitoring completed
□ Daily accuracy report reviewed
□ Deployment retrospective scheduled

ROLLBACK (if needed)
□ Rollback decision documented
□ Helm rollback executed
□ Health verification passed
□ Stakeholders notified
□ Incident report created
```

### B. Version History

| Version | Date | Changes | Deployed By |
|---------|------|---------|-------------|
| v1.0.0 | 2024-12-06 | Initial production release | [Name] |
| | | | |

### C. References

- **TOR Document**: Terms of Reference (TOR) แพลตฟอร์มสำหรับศูนย์ข้อมูลพยากรณ์พลังงานหมุนเวียนของ กฟภ.
- **Architecture Documentation**: `/docs/architecture/overview.md`
- **API Documentation**: `/docs/api/`
- **Helm Chart**: `/infrastructure/helm/pea-re-forecast/`
- **GitLab CI/CD**: `.gitlab-ci.yml`

---

**Document Control**

- **Document ID**: OPS-RUNBOOK-001
- **Version**: 1.0.0
- **Last Reviewed**: December 6, 2024
- **Next Review**: January 6, 2025
- **Owner**: PEA Development Team
- **Approver**: PEA IT Director

---

*This runbook complies with TOR requirements 7.1.4 (CI/CD Deployment), 7.1.5 (Software Licensing), and 7.1.6 (Security and Audit).*
