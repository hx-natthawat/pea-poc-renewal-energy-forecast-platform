# Secrets Management Strategy

**TOR Reference**: Section 7.1.3 - HashiCorp Vault
**Status**: Documented (Deployment Pending)
**Last Updated**: December 6, 2025

---

## Overview

This document outlines the secrets management strategy for the PEA RE Forecast Platform using HashiCorp Vault, as required by TOR Section 7.1.3.

## Secrets Inventory

| Secret Type | Example | Storage Location | Rotation Policy |
|-------------|---------|------------------|-----------------|
| Database Credentials | PostgreSQL password | Vault `secret/pea-forecast/db` | 90 days |
| API Keys | TMD Weather API | Vault `secret/pea-forecast/api-keys` | Annual |
| JWT Signing Keys | Token secrets | Vault `secret/pea-forecast/jwt` | 30 days |
| Keycloak Secrets | Client secrets | Vault `secret/pea-forecast/keycloak` | 90 days |
| TLS Certificates | Ingress certs | cert-manager | Auto-renew |
| LINE Notify Token | Alert webhooks | Vault `secret/pea-forecast/notifications` | Annual |

## Vault Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    HASHICORP VAULT CLUSTER                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐              │
│  │   Vault 1   │  │   Vault 2   │  │   Vault 3   │              │
│  │  (Leader)   │  │  (Standby)  │  │  (Standby)  │              │
│  └─────────────┘  └─────────────┘  └─────────────┘              │
│         │                │                │                      │
│         └────────────────┼────────────────┘                      │
│                          │                                       │
│                    ┌─────┴─────┐                                 │
│                    │  Consul   │                                 │
│                    │  Backend  │                                 │
│                    └───────────┘                                 │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## Kubernetes Integration

### Option 1: Vault Agent Injector (Recommended)

```yaml
# Example pod annotation for secret injection
annotations:
  vault.hashicorp.com/agent-inject: "true"
  vault.hashicorp.com/role: "pea-forecast"
  vault.hashicorp.com/agent-inject-secret-db: "secret/pea-forecast/db"
  vault.hashicorp.com/agent-inject-template-db: |
    {{- with secret "secret/pea-forecast/db" -}}
    DATABASE_URL=postgresql://{{ .Data.data.username }}:{{ .Data.data.password }}@timescaledb:5432/pea_forecast
    {{- end }}
```

### Option 2: Vault CSI Provider

```yaml
# SecretProviderClass for CSI integration
apiVersion: secrets-store.csi.x-k8s.io/v1
kind: SecretProviderClass
metadata:
  name: pea-forecast-secrets
spec:
  provider: vault
  parameters:
    vaultAddress: "http://vault:8200"
    roleName: "pea-forecast"
    objects: |
      - objectName: "db-password"
        secretPath: "secret/data/pea-forecast/db"
        secretKey: "password"
```

## Vault Policies

```hcl
# infrastructure/security/vault/policies/pea-forecast.hcl

# Backend service policy
path "secret/data/pea-forecast/db" {
  capabilities = ["read"]
}

path "secret/data/pea-forecast/redis" {
  capabilities = ["read"]
}

path "secret/data/pea-forecast/keycloak" {
  capabilities = ["read"]
}

# ML service policy
path "secret/data/pea-forecast/mlflow" {
  capabilities = ["read"]
}

# Admin policy for rotation
path "secret/data/pea-forecast/*" {
  capabilities = ["create", "read", "update", "delete", "list"]
}
```

## Kubernetes Auth Configuration

```bash
# Enable Kubernetes auth method
vault auth enable kubernetes

# Configure Kubernetes auth
vault write auth/kubernetes/config \
    kubernetes_host="https://$KUBERNETES_PORT_443_TCP_ADDR:443" \
    token_reviewer_jwt="$(cat /var/run/secrets/kubernetes.io/serviceaccount/token)" \
    kubernetes_ca_cert=@/var/run/secrets/kubernetes.io/serviceaccount/ca.crt

# Create role for pea-forecast namespace
vault write auth/kubernetes/role/pea-forecast \
    bound_service_account_names=default,backend,ml-service \
    bound_service_account_namespaces=pea-forecast-staging,pea-forecast-prod \
    policies=pea-forecast \
    ttl=1h
```

## Secret Rotation Procedures

### Database Credentials

```bash
# 1. Generate new password
NEW_PASSWORD=$(openssl rand -base64 32)

# 2. Update Vault
vault kv put secret/pea-forecast/db \
    username=postgres \
    password=$NEW_PASSWORD

# 3. Update PostgreSQL
psql -c "ALTER USER postgres WITH PASSWORD '$NEW_PASSWORD';"

# 4. Restart pods to pick up new secrets
kubectl rollout restart deployment/backend -n pea-forecast-prod
```

### JWT Signing Keys

```bash
# 1. Generate new key pair
openssl genrsa -out jwt-private.pem 4096
openssl rsa -in jwt-private.pem -pubout -out jwt-public.pem

# 2. Update Vault
vault kv put secret/pea-forecast/jwt \
    private_key=@jwt-private.pem \
    public_key=@jwt-public.pem

# 3. Restart backend
kubectl rollout restart deployment/backend -n pea-forecast-prod
```

## Pre-Production Checklist

- [ ] Deploy Vault HA cluster (3 nodes minimum)
- [ ] Configure Consul backend for HA
- [ ] Enable audit logging
- [ ] Configure auto-unseal (AWS KMS, Azure Key Vault, or GCP KMS)
- [ ] Set up Kubernetes auth method
- [ ] Create service account policies
- [ ] Initialize secrets for all services
- [ ] Configure secret rotation schedules
- [ ] Test failover scenarios
- [ ] Document emergency procedures

## Deployment Commands

```bash
# Add HashiCorp Helm repo
helm repo add hashicorp https://helm.releases.hashicorp.com
helm repo update

# Deploy Vault in HA mode
helm install vault hashicorp/vault \
    --namespace vault \
    --create-namespace \
    --set server.ha.enabled=true \
    --set server.ha.replicas=3 \
    --set injector.enabled=true \
    --set csi.enabled=true
```

## References

- [Vault Kubernetes Integration](https://developer.hashicorp.com/vault/docs/platform/k8s)
- [Vault Agent Injector](https://developer.hashicorp.com/vault/docs/platform/k8s/injector)
- [TOR Section 7.1.3](./CLAUDE.md#required-software-stack-per-tor)

---

*Document Version: 1.0*
*Status: Strategy Documented, Deployment Pending*
