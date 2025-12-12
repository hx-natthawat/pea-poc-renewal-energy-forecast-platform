# Pre-Deployment Checklist

> **Version**: 1.0.0
> **Last Updated**: December 2025
> **Use Case**: Run this checklist before staging/production deployment

## Quick Summary

| Category | Items | Required For |
|----------|-------|--------------|
| Code Quality | 6 | All deployments |
| Security | 8 | All deployments |
| Infrastructure | 7 | All deployments |
| Data/ML | 5 | All deployments |
| Operations | 6 | Production only |

---

## 1. Code Quality

### Tests
- [ ] All unit tests pass: `pytest tests/unit/ -v`
- [ ] All integration tests pass: `pytest tests/integration/ -v`
- [ ] All E2E tests pass: `npx playwright test`
- [ ] Test coverage >= 80%: `pytest --cov=app --cov-report=term`

### Linting & Formatting
- [ ] Backend linting passes: `ruff check app/`
- [ ] Frontend linting passes: `pnpm run lint`

---

## 2. Security

### Vulnerability Scanning
- [ ] No critical CVEs in dependencies: `npm audit` / `pip audit`
- [ ] Container images scanned: `trivy image <image>`
- [ ] No secrets in code: `detect-secrets scan`

### Configuration
- [ ] AUTH_ENABLED=true in production
- [ ] DEBUG=false in production
- [ ] CORS origins restricted to allowed domains
- [ ] Rate limiting configured
- [ ] SSL/TLS certificates valid

---

## 3. Infrastructure

### Kubernetes
- [ ] Helm charts lint successfully: `helm lint`
- [ ] Resource limits set (CPU/Memory)
- [ ] PodDisruptionBudgets configured
- [ ] NetworkPolicies applied
- [ ] Ingress configured with TLS

### Database
- [ ] Migrations applied: `alembic upgrade head`
- [ ] Indexes exist for common queries
- [ ] Connection pooling configured
- [ ] Backup strategy documented

---

## 4. Data & ML Models

### Models
- [ ] Solar model file exists: `ml/models/solar_xgb_v1.joblib`
- [ ] Voltage model file exists: `ml/models/voltage_rf_v1.joblib`
- [ ] Model versions match expected

### Performance
- [ ] Solar MAPE < 10% (TOR requirement)
- [ ] Voltage MAE < 2V (TOR requirement)
- [ ] API latency P95 < 500ms

---

## 5. Operations (Production Only)

### Monitoring
- [ ] Prometheus scraping endpoints
- [ ] Grafana dashboards imported
- [ ] Alert rules configured
- [ ] Log aggregation active

### Runbooks
- [ ] Deployment runbook reviewed
- [ ] Rollback procedure tested
- [ ] Incident response contacts documented
- [ ] On-call schedule established

---

## Deployment Commands

### Staging Deployment
```bash
# 1. Run smoke test on current environment
./scripts/smoke-test.sh http://staging-api:8000

# 2. Deploy via Helm
helm upgrade --install pea-forecast \
  ./infrastructure/helm/pea-re-forecast \
  -f ./infrastructure/helm/pea-re-forecast/values-staging.yaml \
  -n pea-forecast-staging

# 3. Verify deployment
kubectl rollout status deployment/backend -n pea-forecast-staging
./scripts/smoke-test.sh http://staging-api:8000
```

### Production Deployment
```bash
# 1. Final smoke test on staging
./scripts/smoke-test.sh http://staging-api:8000

# 2. Create release tag
git tag -a v1.x.x -m "Release v1.x.x"
git push origin v1.x.x

# 3. Deploy via ArgoCD (GitOps)
# ArgoCD will auto-sync from tagged release

# 4. Verify production
./scripts/smoke-test.sh http://prod-api:8000
```

---

## Sign-Off

| Role | Name | Date | Signature |
|------|------|------|-----------|
| Developer | | | |
| Tech Lead | | | |
| QA | | | |
| Ops | | | |

---

## Checklist History

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2025-12-13 | Initial checklist |
