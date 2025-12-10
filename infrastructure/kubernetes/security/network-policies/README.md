# Network Policies - Zero-Trust Networking

TOR Requirement: **7.1.3 - Cilium CNI** for zero-trust network segmentation.

## Overview

These network policies implement a zero-trust security model where:
- **All traffic is denied by default**
- **Only explicitly allowed traffic is permitted**
- **Pods can only communicate with their required dependencies**

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                     NETWORK POLICY ARCHITECTURE                              │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│    INTERNET                                                                  │
│        │                                                                     │
│        ▼                                                                     │
│  ┌──────────────┐                                                           │
│  │   INGRESS    │  (Kong/Nginx)                                             │
│  │  CONTROLLER  │                                                           │
│  └──────┬───────┘                                                           │
│         │                                                                    │
│         │ :3000                    :8000                                     │
│         ▼                          ▼                                         │
│  ┌──────────────┐           ┌──────────────┐                                │
│  │   FRONTEND   │──────────▶│   BACKEND    │                                │
│  │  (Next.js)   │  :8000    │  (FastAPI)   │                                │
│  └──────────────┘           └──────┬───────┘                                │
│                                    │                                         │
│              ┌─────────────────────┼─────────────────────┐                  │
│              │                     │                     │                   │
│              ▼ :5432               ▼ :6379               ▼ :8200            │
│       ┌──────────────┐      ┌──────────────┐      ┌──────────────┐         │
│       │ TIMESCALEDB  │      │    REDIS     │      │    VAULT     │         │
│       │              │      │              │      │  (vault ns)  │         │
│       └──────────────┘      └──────────────┘      └──────────────┘         │
│                                                                              │
│    ════════════════════════════════════════════════════════════════         │
│                          pea-forecast namespace                              │
│    ════════════════════════════════════════════════════════════════         │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘

LEGEND:
  ───▶  Allowed traffic (network policy rule)
  :XXXX Port number
```

## Policy Files

| File | Target | Description |
|------|--------|-------------|
| `default-deny.yaml` | All pods | Denies all ingress/egress by default |
| `backend-policy.yaml` | Backend API | Allows frontend→backend, backend→db/redis/vault |
| `frontend-policy.yaml` | Frontend | Allows ingress→frontend, frontend→backend |
| `database-policy.yaml` | TimescaleDB + Redis | Allows backend→database only |
| `vault-policy.yaml` | Vault | Allows backend→vault, vault→K8s API |

## Deployment

### Prerequisites

- Kubernetes cluster with CNI supporting NetworkPolicy (Cilium, Calico, etc.)
- Namespace labels configured:
  ```bash
  kubectl label namespace pea-forecast kubernetes.io/metadata.name=pea-forecast
  kubectl label namespace vault kubernetes.io/metadata.name=vault
  ```

### Apply Policies

```bash
# Apply all network policies
kubectl apply -f infrastructure/kubernetes/security/network-policies/

# Verify policies
kubectl get networkpolicies -n pea-forecast
kubectl get networkpolicies -n vault
```

### Verify Connectivity

```bash
# Test backend can reach database
kubectl exec -n pea-forecast deploy/backend -- nc -zv timescaledb 5432

# Test frontend can reach backend
kubectl exec -n pea-forecast deploy/frontend -- nc -zv backend 8000

# Test backend can reach Vault
kubectl exec -n pea-forecast deploy/backend -- nc -zv vault.vault.svc.cluster.local 8200
```

## Cilium-Specific Policies (Optional)

For enhanced security with Cilium, you can also use CiliumNetworkPolicy CRDs:

```yaml
apiVersion: cilium.io/v2
kind: CiliumNetworkPolicy
metadata:
  name: backend-l7-policy
  namespace: pea-forecast
spec:
  endpointSelector:
    matchLabels:
      app.kubernetes.io/name: backend
  egress:
    - toEndpoints:
        - matchLabels:
            app.kubernetes.io/name: timescaledb
      toPorts:
        - ports:
            - port: "5432"
              protocol: TCP
          rules:
            l7proto: postgres
```

## Troubleshooting

### Traffic Blocked Unexpectedly

1. Check if policies exist:
   ```bash
   kubectl get networkpolicies -n pea-forecast -o wide
   ```

2. Verify pod labels match policy selectors:
   ```bash
   kubectl get pods -n pea-forecast --show-labels
   ```

3. Check Cilium policy enforcement (if using Cilium):
   ```bash
   kubectl exec -n kube-system cilium-xxx -- cilium policy get
   ```

### Common Issues

| Issue | Cause | Solution |
|-------|-------|----------|
| DNS resolution fails | DNS egress not allowed | Ensure DNS egress rule exists |
| Backend can't reach DB | Wrong pod labels | Verify `app.kubernetes.io/name` labels |
| External API calls fail | Egress to internet blocked | Add ipBlock rule for external IPs |

## Security Considerations

1. **Default Deny**: Always start with default deny to prevent accidental exposure
2. **Least Privilege**: Only allow traffic that is absolutely necessary
3. **Namespace Isolation**: Use namespace selectors to isolate workloads
4. **Audit Logging**: Enable network policy audit logging in production
5. **Regular Review**: Review and update policies as architecture evolves

## Integration with Helm

Network policies can be enabled/disabled via Helm values:

```yaml
# values.yaml
networkPolicy:
  enabled: true  # Set to true for production
```

When `networkPolicy.enabled: true`, the Helm chart will deploy these policies automatically.
