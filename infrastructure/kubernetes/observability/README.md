# Observability Stack

TOR Requirements: **Prometheus, Grafana, Jaeger, Opensearch, Fluentbit, Sentry**

## Overview

The observability stack provides comprehensive monitoring, alerting, and visualization for the PEA RE Forecast Platform.

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                      OBSERVABILITY ARCHITECTURE                              │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌─────────────────┐                                                         │
│  │  PEA FORECAST   │                                                         │
│  │   NAMESPACE     │                                                         │
│  │                 │                                                         │
│  │  ┌───────────┐  │   /metrics                                             │
│  │  │  Backend  │──┼───────────────────────────┐                            │
│  │  └───────────┘  │                           │                            │
│  │  ┌───────────┐  │                           │                            │
│  │  │ Frontend  │──┼───────────────────────────┤                            │
│  │  └───────────┘  │                           │                            │
│  │  ┌───────────┐  │                           │                            │
│  │  │TimescaleDB│──┼───────────────────────────┤                            │
│  │  └───────────┘  │                           │                            │
│  │  ┌───────────┐  │                           │                            │
│  │  │   Redis   │──┼───────────────────────────┤                            │
│  │  └───────────┘  │                           ▼                            │
│  └─────────────────┘                  ┌─────────────────┐                   │
│                                       │   PROMETHEUS    │                   │
│                                       │                 │                   │
│                                       │  Scrape: 15s    │                   │
│                                       │  Retention: 15d │                   │
│                                       └────────┬────────┘                   │
│                                                │                            │
│                    ┌───────────────────────────┼───────────────────────────┐│
│                    │                           │                           ││
│                    ▼                           ▼                           ▼│
│           ┌─────────────────┐        ┌─────────────────┐        ┌──────────┐│
│           │    GRAFANA      │        │  ALERTMANAGER   │        │  JAEGER  ││
│           │                 │        │                 │        │          ││
│           │ Dashboards:     │        │ Routes:         │        │  Tracing ││
│           │ - API Metrics   │        │ - Critical      │        │          ││
│           │ - ML Accuracy   │        │ - ML Team       │        │          ││
│           │ - Voltage       │        │ - Operations    │        │          ││
│           │ - Infrastructure│        │ - Platform      │        │          ││
│           └─────────────────┘        └────────┬────────┘        └──────────┘│
│                                               │                             │
│                                               ▼                             │
│                                      ┌─────────────────┐                    │
│                                      │   NOTIFICATIONS │                    │
│                                      │                 │                    │
│                                      │ - Webhook (API) │                    │
│                                      │ - Email         │                    │
│                                      │ - LINE Notify   │                    │
│                                      └─────────────────┘                    │
│                                                                              │
│  ════════════════════════════════════════════════════════════════════════   │
│                            monitoring namespace                              │
│  ════════════════════════════════════════════════════════════════════════   │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Components

| Component | Version | Port | Purpose |
|-----------|---------|------|---------|
| Prometheus | v2.48.0 | 9090 | Metrics collection |
| Grafana | v10.2.0 | 3000 | Visualization |
| AlertManager | v0.26.0 | 9093 | Alert routing |

## Deployment

### Prerequisites

```bash
# Ensure namespace exists
kubectl apply -f namespace.yaml

# Label pea-forecast namespace for pod discovery
kubectl label namespace pea-forecast prometheus-scrape=enabled
```

### Deploy Components

```bash
# Deploy Prometheus
kubectl apply -f prometheus/

# Deploy Grafana
kubectl apply -f grafana/

# Deploy AlertManager
kubectl apply -f alertmanager/
```

### Access Dashboards

**Development (NodePort)**:
- Prometheus: http://localhost:30090
- Grafana: http://localhost:30030
- AlertManager: http://localhost:9093

**Production (Ingress)**:
- Prometheus: https://prometheus.pea-forecast.pea.co.th
- Grafana: https://grafana.pea-forecast.pea.co.th

### Default Credentials

| Service | Username | Password |
|---------|----------|----------|
| Grafana | admin | pea-forecast-admin |

**Important**: Change default passwords in production!

## Alert Rules

### API Alerts

| Alert | Condition | Severity |
|-------|-----------|----------|
| APIHighLatency | p95 > 500ms for 5m | warning |
| APIHighErrorRate | 5xx > 5% for 5m | critical |
| BackendPodDown | No healthy pods for 2m | critical |

### ML Model Alerts

| Alert | Condition | Severity |
|-------|-----------|----------|
| SolarForecastHighMAPE | MAPE > 10% for 15m | warning |
| VoltageHighMAE | MAE > 2V for 15m | warning |
| ModelInferenceSlowdown | p95 > 1s for 5m | warning |

### Voltage Alerts

| Alert | Condition | Severity |
|-------|-----------|----------|
| VoltageOverLimit | > 242V for 1m | critical |
| VoltageUnderLimit | < 218V for 1m | critical |
| TooManyVoltageAlerts | > 50 alerts/hour | warning |

### Infrastructure Alerts

| Alert | Condition | Severity |
|-------|-----------|----------|
| DatabaseConnectionFailure | 0 connections for 1m | critical |
| DatabaseSlowQueries | p95 > 1s for 5m | warning |
| PodHighMemoryUsage | > 85% for 5m | warning |
| PodHighCPUUsage | > 80% for 5m | warning |

## Alert Routing

```
Default → Webhook to Backend API
    │
    ├── Critical → Immediate notification (10s group wait)
    │               + LINE Notify (production)
    │
    ├── ML Team → ML-specific receiver
    │
    ├── Operations → Operations team receiver
    │               (voltage alerts)
    │
    └── Platform → Platform team receiver
                  (API, infrastructure)
```

## Metrics Exposed

### Backend API Metrics

The FastAPI backend exposes metrics at `/metrics`:

```
# HTTP Request metrics
http_requests_total{method, endpoint, status}
http_request_duration_seconds{method, endpoint}

# Database metrics
pea_database_connections_active
pea_database_query_duration_seconds

# Redis metrics
pea_redis_connected
pea_redis_operations_total

# Model metrics
pea_solar_forecast_mape
pea_voltage_prediction_mae
pea_model_inference_duration_seconds

# Business metrics
pea_prosumer_voltage{prosumer_id, phase}
pea_voltage_alerts_total
```

## Grafana Dashboards

### Pre-configured Dashboards

1. **API Overview**
   - Request rate and latency
   - Error rates by endpoint
   - Active connections

2. **ML Model Performance**
   - Solar forecast accuracy (MAPE)
   - Voltage prediction accuracy (MAE)
   - Inference latency

3. **Voltage Monitoring**
   - Real-time voltage by prosumer
   - Alert timeline
   - Phase distribution

4. **Infrastructure**
   - Pod resource usage
   - Database performance
   - Redis cache hit rate

## Production Configuration

### Enable Email Alerts

Edit `alertmanager/alertmanager-deployment.yaml`:

```yaml
global:
  smtp_smarthost: 'smtp.pea.co.th:587'
  smtp_from: 'alerts@pea-forecast.pea.co.th'
  smtp_auth_username: 'alertmanager'
  smtp_auth_password: 'secret'
```

### Enable LINE Notify

Add to AlertManager receivers:

```yaml
receivers:
  - name: 'critical-receiver'
    webhook_configs:
      - url: 'https://notify-api.line.me/api/notify'
        http_config:
          bearer_token: '<LINE_NOTIFY_TOKEN>'
```

### Persistent Storage

For production, add PVC to Prometheus:

```yaml
volumes:
  - name: storage
    persistentVolumeClaim:
      claimName: prometheus-data
```

## Troubleshooting

### Prometheus Not Scraping

1. Check ServiceMonitor labels match:
   ```bash
   kubectl get servicemonitor -n monitoring
   ```

2. Verify pod annotations:
   ```bash
   kubectl get pods -n pea-forecast -o jsonpath='{.items[*].metadata.annotations}'
   ```

3. Check Prometheus targets:
   http://localhost:30090/targets

### Grafana Dashboard Not Loading

1. Verify datasource:
   ```bash
   kubectl logs -n monitoring deploy/grafana
   ```

2. Check Prometheus connectivity:
   ```bash
   kubectl exec -n monitoring deploy/grafana -- curl -s prometheus:9090/-/healthy
   ```

### Alerts Not Firing

1. Check alert rules:
   http://localhost:30090/alerts

2. Verify AlertManager config:
   ```bash
   kubectl exec -n monitoring deploy/alertmanager -- cat /etc/alertmanager/alertmanager.yml
   ```
