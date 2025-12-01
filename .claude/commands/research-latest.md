# Research Latest Versions

You are a technology research expert for the PEA RE Forecast Platform.

## Task
Research and document the latest stable versions of all project dependencies.

## Instructions

1. **Web Search for Latest Versions**:
   Use WebSearch tool to find current stable versions of:

   ### Core Runtime
   - Python (3.11.x or 3.12.x?)
   - Node.js LTS
   - Ubuntu LTS

   ### Databases
   - PostgreSQL
   - TimescaleDB
   - Redis

   ### Kubernetes Stack
   - Kubernetes
   - Kind (for local)
   - Helm
   - Cilium

   ### ML Libraries
   - TensorFlow
   - XGBoost
   - scikit-learn
   - pandas
   - pvlib (solar modeling)
   - pandapower (power flow)

   ### Backend
   - FastAPI
   - Pydantic
   - SQLAlchemy
   - asyncpg
   - uvicorn

   ### Frontend
   - React
   - Next.js
   - TypeScript
   - Tailwind CSS
   - shadcn/ui

   ### Observability
   - Prometheus
   - Grafana
   - Jaeger
   - OpenSearch

2. **Compatibility Check**:
   - Verify version compatibility
   - Check breaking changes
   - Note security advisories

3. **Output**:
   - Update `docs/specs/dependency-versions.md`
   - Create/update `requirements.txt` files
   - Create/update `package.json`

## Version Documentation Format

```markdown
# Dependency Versions

Last Updated: [DATE]

## Core
| Package | Version | EOL Date | Notes |
|---------|---------|----------|-------|
| Python | 3.12.x | 2028-10 | Latest stable |

## Verified Compatibility Matrix
[Which versions work together]
```
