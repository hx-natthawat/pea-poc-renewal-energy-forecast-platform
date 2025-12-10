# TLS Certificate Management with cert-manager

TOR Requirement: **7.1.3 - Secure Communications**

## Overview

This directory contains configurations for automated TLS certificate management using cert-manager.

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                       TLS CERTIFICATE ARCHITECTURE                          │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                         CERT-MANAGER                                 │   │
│  │                                                                      │   │
│  │  ┌───────────────────┐    ┌───────────────────┐                     │   │
│  │  │  ClusterIssuer    │    │  ClusterIssuer    │                     │   │
│  │  │  (Let's Encrypt   │    │  (Let's Encrypt   │                     │   │
│  │  │   Staging)        │    │   Production)     │                     │   │
│  │  └─────────┬─────────┘    └─────────┬─────────┘                     │   │
│  │            │                        │                                │   │
│  │            └────────────┬───────────┘                                │   │
│  │                         │                                            │   │
│  │                         ▼                                            │   │
│  │            ┌───────────────────────┐                                 │   │
│  │            │   Certificate         │                                 │   │
│  │            │   Resources           │                                 │   │
│  │            │                       │                                 │   │
│  │            │ - pea-forecast-tls    │                                 │   │
│  │            │ - grafana-tls         │                                 │   │
│  │            │ - vault-tls           │                                 │   │
│  │            └───────────┬───────────┘                                 │   │
│  │                        │                                             │   │
│  └────────────────────────┼─────────────────────────────────────────────┘   │
│                           │                                                 │
│                           ▼                                                 │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                      KUBERNETES SECRETS                              │   │
│  │                                                                      │   │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐                  │   │
│  │  │ pea-tls     │  │ grafana-tls │  │ vault-tls   │                  │   │
│  │  │ Secret      │  │ Secret      │  │ Secret      │                  │   │
│  │  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘                  │   │
│  │         │                │                │                          │   │
│  └─────────┼────────────────┼────────────────┼──────────────────────────┘   │
│            │                │                │                              │
│            ▼                ▼                ▼                              │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                         INGRESS CONTROLLER                           │   │
│  │                                                                      │   │
│  │  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐      │   │
│  │  │ pea-forecast    │  │ grafana         │  │ vault           │      │   │
│  │  │ Ingress         │  │ Ingress         │  │ Ingress         │      │   │
│  │  │                 │  │                 │  │                 │      │   │
│  │  │ TLS: pea-tls    │  │ TLS: grafana-tls│  │ TLS: vault-tls  │      │   │
│  │  └─────────────────┘  └─────────────────┘  └─────────────────┘      │   │
│  │                                                                      │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│                              HTTPS Traffic                                  │
│                                   │                                         │
│                                   ▼                                         │
│                         ┌─────────────────┐                                 │
│                         │   End Users     │                                 │
│                         └─────────────────┘                                 │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Components

| Component | Purpose | Version |
|-----------|---------|---------|
| cert-manager | Certificate lifecycle management | v1.14.x |
| ClusterIssuer | Let's Encrypt ACME integration | - |
| Certificate | TLS certificate resources | - |

## Prerequisites

### Install cert-manager

```bash
# Add Jetstack Helm repository
helm repo add jetstack https://charts.jetstack.io
helm repo update

# Install cert-manager with CRDs
helm install cert-manager jetstack/cert-manager \
  --namespace cert-manager \
  --create-namespace \
  --version v1.14.4 \
  --set installCRDs=true
```

### Verify Installation

```bash
kubectl get pods -n cert-manager
kubectl get crd | grep cert-manager
```

## Deployment

### 1. Create ClusterIssuers

```bash
# Apply ClusterIssuers (staging first for testing)
kubectl apply -f cluster-issuer.yaml
```

### 2. Create Certificates

```bash
# Apply Certificate resources
kubectl apply -f certificates.yaml
```

### 3. Verify Certificates

```bash
# Check certificate status
kubectl get certificates -n pea-forecast
kubectl describe certificate pea-forecast-tls -n pea-forecast
```

## Configuration

### ClusterIssuer Options

| Issuer | Purpose | Rate Limits |
|--------|---------|-------------|
| `letsencrypt-staging` | Testing (not trusted) | Higher limits |
| `letsencrypt-production` | Production (trusted) | 50 certs/week/domain |

### Certificate Domains

| Service | Domain | Namespace |
|---------|--------|-----------|
| PEA Forecast API | `api.pea-forecast.pea.co.th` | pea-forecast |
| PEA Forecast UI | `pea-forecast.pea.co.th` | pea-forecast |
| Grafana | `grafana.pea-forecast.pea.co.th` | monitoring |
| Prometheus | `prometheus.pea-forecast.pea.co.th` | monitoring |
| Vault | `vault.pea-forecast.pea.co.th` | vault |

## Self-Signed Certificates (Development)

For development/staging environments without public DNS:

```bash
# Apply self-signed issuer
kubectl apply -f self-signed-issuer.yaml

# Generate self-signed certificates
kubectl apply -f certificates-dev.yaml
```

## Troubleshooting

### Certificate Not Ready

```bash
# Check certificate status
kubectl describe certificate pea-forecast-tls -n pea-forecast

# Check cert-manager logs
kubectl logs -n cert-manager -l app=cert-manager

# Check challenge status
kubectl get challenges -n pea-forecast
kubectl describe challenge <challenge-name> -n pea-forecast
```

### Common Issues

1. **DNS not resolving**: Ensure DNS records point to ingress IP
2. **Rate limited**: Switch to staging issuer for testing
3. **Challenge failed**: Check ingress controller is accessible on port 80

### Certificate Renewal

cert-manager automatically renews certificates 30 days before expiry.

```bash
# Check renewal status
kubectl get certificate -A -o wide

# Force renewal (if needed)
kubectl delete secret pea-forecast-tls -n pea-forecast
```

## Security Notes

- Private keys are stored in Kubernetes Secrets
- Use Vault for additional key protection in production
- Enable TLS 1.2+ only (configured in Ingress)
- Rotate certificates before expiry

## Integration with Kong Ingress

Kong Ingress Controller automatically picks up TLS secrets:

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: pea-forecast
  annotations:
    cert-manager.io/cluster-issuer: "letsencrypt-production"
spec:
  tls:
    - hosts:
        - pea-forecast.pea.co.th
      secretName: pea-forecast-tls
```
