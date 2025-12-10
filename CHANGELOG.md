# Changelog

All notable changes to the PEA RE Forecast Platform will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.1.0] - 2025-12-10

### Added

#### Core Features
- **Weather API Integration**: TMD (Thai Meteorological Department) API with fallback simulation
- **Model Retraining Pipeline**: Automated drift detection and A/B testing for ML models
- **Multi-Channel Alerting (F002)**: Email and LINE Notify notifications
- **Multi-Region Support (F003)**: 4 PEA zones (Central, Northeast, South, North) with RBAC
- **Audit Log UI (TOR 7.1.6)**: Full viewer with filters, export, and statistics

#### Grid Operations (TOR 7.5)
- Load Forecast API (`/api/v1/load-forecast/predict`) - TOR 7.5.1.3
- Demand Forecast API (`/api/v1/demand-forecast/predict`) - TOR 7.5.1.2
- Imbalance Forecast API (`/api/v1/imbalance-forecast/predict`) - TOR 7.5.1.4
- Grid Operations dashboard tab with Load/Demand/Imbalance visualizations

#### Infrastructure (TOR 7.1.3, 7.1.6, Table 2)
- **HashiCorp Vault**: Secrets management with Kubernetes auth method
- **Network Policies**: Zero-trust networking with default deny
- **Observability Stack**: Prometheus v3.8.0, Grafana v12.3.0, AlertManager v0.29.0
- **TLS/cert-manager**: Let's Encrypt production + self-signed dev certificates
- Pre-configured Grafana dashboards (K8s Overview, PEA Alerts)

#### Documentation
- Client handover checklist (`docs/CLIENT-HANDOVER-CHECKLIST.md`)
- Staging deployment script (`scripts/deploy-staging.sh`)
- Development roadmap (`docs/roadmaps/dev-roadmap.md`)

### Changed
- Updated test count from 719 to 727 (672 backend + 55 frontend)
- Improved Help system with inline tooltips and brand colors
- Enhanced error handling with ErrorBoundary and ErrorBanner components

### Fixed
- Next.js CVE-2024-XXXXX (RCE vulnerability) - upgraded to 16.0.7
- JWT error information leakage - generic error messages
- CORS wildcard configuration - explicit allow lists
- Missing OWASP security headers

### Security
- All HIGH/CRITICAL vulnerabilities resolved
- Security headers middleware (X-Frame-Options, X-Content-Type-Options, HSTS)
- Explicit CORS configuration
- Hardened JWT error handling

## [1.0.0] - 2025-12-04

### Added

#### Core Functionality
- **Solar Power Forecast (F1)**: MAPE 9.74% (target <10%), RMSE compliant
- **Voltage Prediction (F5)**: MAE 0.036V (target <2V)
- Complete API endpoints for forecasting
- WebSocket real-time updates

#### Frontend Dashboard
- Solar Forecast visualization with confidence intervals
- Voltage Monitoring with network topology overlay
- Alert Dashboard with timeline
- Historical Analysis with CSV/Excel export
- Day-Ahead Report generation
- Forecast Comparison charts
- Model Performance monitoring

#### Infrastructure
- Helm charts for Kubernetes deployment
- GitLab CI/CD pipeline
- ArgoCD GitOps configuration
- Load testing with Locust (300K users)

#### Security
- Keycloak authentication integration
- JWT validation middleware
- Security scanning (Trivy, SonarQube)

### Performance
- API Latency: P95 = 38ms (target <500ms)
- Supports 2,000+ RE plants
- Load tested for 300,000+ consumers

---

## TOR Compliance Summary

| Requirement | Version | Status |
|-------------|---------|--------|
| Solar MAPE < 10% | 1.0.0 | PASS (9.74%) |
| Voltage MAE < 2V | 1.0.0 | PASS (0.036V) |
| API Latency < 500ms | 1.0.0 | PASS (P95=38ms) |
| 2,000+ RE Plants | 1.0.0 | PASS |
| 300,000+ Consumers | 1.0.0 | PASS |
| Audit Trail (7.1.6) | 1.1.0 | PASS |
| Secrets Management (Table 2) | 1.1.0 | PASS |
| Network Policies (7.1.3) | 1.1.0 | PASS |
| Observability (Table 2) | 1.1.0 | PASS |
| TLS/cert-manager (7.1.3) | 1.1.0 | PASS |

---

[1.1.0]: https://gitlab.pea.co.th/pea-re-forecast/pea-re-forecast-platform/compare/v1.0.0...v1.1.0
[1.0.0]: https://gitlab.pea.co.th/pea-re-forecast/pea-re-forecast-platform/releases/tag/v1.0.0
