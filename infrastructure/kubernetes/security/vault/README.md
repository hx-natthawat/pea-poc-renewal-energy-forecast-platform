# HashiCorp Vault - PEA RE Forecast Platform

Secrets management using HashiCorp Vault per TOR Table 2 requirements.

## Quick Start

### Deploy Vault to Kubernetes

```bash
# Create namespace and deploy
kubectl apply -f namespace.yaml
kubectl apply -f vault-config.yaml
kubectl apply -f vault-deployment.yaml

# Wait for Vault to be ready
kubectl wait --for=condition=ready pod -l app=vault -n vault --timeout=120s

# Initialize and configure Vault
kubectl apply -f vault-init-job.yaml

# Check init job status
kubectl logs -n vault job/vault-init
```

### Access Vault UI

```bash
# Port forward (alternative to NodePort)
kubectl port-forward -n vault svc/vault 8200:8200

# Or use NodePort
# http://localhost:30820
```

### Secrets Structure

```
pea-forecast/
├── database
│   ├── DB_USER
│   ├── DB_PASSWORD
│   ├── DB_HOST
│   ├── DB_PORT
│   ├── DB_NAME
│   └── DATABASE_URL
├── redis
│   ├── REDIS_HOST
│   ├── REDIS_PORT
│   ├── REDIS_PASSWORD
│   └── REDIS_URL
├── app
│   ├── APP_SECRET_KEY
│   ├── JWT_SECRET_KEY
│   └── ENCRYPTION_KEY
└── keycloak
    ├── KEYCLOAK_URL
    ├── KEYCLOAK_REALM
    ├── KEYCLOAK_CLIENT_ID
    └── KEYCLOAK_CLIENT_SECRET
```

## Backend Integration

### Option 1: Vault Agent Injector (Recommended)

Add annotations to backend deployment:

```yaml
annotations:
  vault.hashicorp.com/agent-inject: "true"
  vault.hashicorp.com/role: "pea-forecast-backend"
  vault.hashicorp.com/agent-inject-secret-database: "pea-forecast/data/database"
  vault.hashicorp.com/agent-inject-template-database: |
    {{- with secret "pea-forecast/data/database" -}}
    export DATABASE_URL="{{ .Data.data.DATABASE_URL }}"
    {{- end }}
```

### Option 2: HVAC Python Library

```python
import hvac

client = hvac.Client(url='http://vault:8200')
client.auth.kubernetes.login(role='pea-forecast-backend')

# Read secrets
secret = client.secrets.kv.v2.read_secret_version(
    path='database',
    mount_point='pea-forecast'
)
database_url = secret['data']['data']['DATABASE_URL']
```

## Production Considerations

1. **High Availability**: Use 3+ replicas with Raft storage
2. **Auto-Unseal**: Configure auto-unseal with cloud KMS
3. **TLS**: Enable TLS with cert-manager certificates
4. **Backup**: Regular backup of storage backend
5. **Audit**: Audit logs should be shipped to Opensearch

## TOR Compliance

| Requirement | Implementation |
|-------------|---------------|
| TOR 7.1.6 Audit | Vault audit logging enabled |
| TOR Table 2 | HashiCorp Vault deployed |
| Key Management | All secrets in Vault |
