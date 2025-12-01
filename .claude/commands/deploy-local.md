# Deploy to Local Kind Cluster

You are a Kubernetes deployment expert for the PEA RE Forecast Platform.

## Task
Deploy the platform to a local Kind (Kubernetes in Docker) cluster for testing.

## Prerequisites Check

```bash
# Check required tools
which docker && docker --version
which kind && kind --version
which kubectl && kubectl version --client
which helm && helm version
```

## Instructions

1. **Research Latest Versions**:
   - Check Kind latest version
   - Check Helm chart dependencies versions
   - Verify container image compatibility

2. **Create Kind Cluster**:
   ```bash
   # kind-config.yaml
   kind: Cluster
   apiVersion: kind.x-k8s.io/v1alpha4
   nodes:
   - role: control-plane
     extraPortMappings:
     - containerPort: 30080
       hostPort: 8080
     - containerPort: 30443
       hostPort: 8443
   - role: worker
   - role: worker
   ```

3. **Deploy Stack**:
   - TimescaleDB (PostgreSQL + TimescaleDB extension)
   - Redis
   - Backend (FastAPI)
   - Frontend (React/Next.js)
   - Kong API Gateway (optional for local)

4. **Validation Steps**:
   ```bash
   # Check all pods running
   kubectl get pods -n pea-forecast

   # Check services
   kubectl get svc -n pea-forecast

   # Test API health
   curl http://localhost:8080/api/v1/health

   # Test database connection
   kubectl exec -it timescaledb-0 -n pea-forecast -- psql -U postgres -c "SELECT version();"
   ```

5. **Output**:
   - Update `docs/guides/local-deployment.md`
   - Log deployment status to `docs/plans/deployment-log.md`

## Cleanup

```bash
kind delete cluster --name pea-forecast
```
