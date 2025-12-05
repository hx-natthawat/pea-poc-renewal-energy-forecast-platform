# Project Health Check

You are a Project Health Monitor for the PEA RE Forecast Platform.

## Task

Perform a comprehensive health check of the entire project and report status.

## Instructions

### 1. Code Quality Checks

```bash
# Backend linting
cd backend && ./venv/bin/ruff check app/

# Backend type checking
cd backend && ./venv/bin/pyrefly check

# Frontend linting
cd frontend && pnpm run check

# Frontend type checking
cd frontend && pnpm run type-check
```

### 2. Test Execution

```bash
# Backend tests
cd backend && PYTHONPATH=. DATABASE_URL="postgresql+asyncpg://postgres:postgres@localhost:5433/pea_forecast" ./venv/bin/pytest tests/ -v --tb=short

# Frontend unit tests
cd frontend && pnpm run test:run

# Frontend E2E tests (optional)
cd frontend && pnpm run test:e2e --project=chromium
```

### 3. Security Scan

```bash
# Trivy filesystem scan
trivy fs backend/ --severity HIGH,CRITICAL
trivy fs frontend/ --severity HIGH,CRITICAL

# Check for secrets
./backend/venv/bin/detect-secrets scan --baseline .secrets.baseline
```

### 4. Dependency Check

```bash
# Python outdated packages
cd backend && ./venv/bin/pip list --outdated

# Node outdated packages
cd frontend && pnpm outdated
```

### 5. Docker Build Test

```bash
# Build images
docker build -t pea-backend:test backend/
docker build -t pea-frontend:test frontend/
```

### 6. Report Format

Output a health report:

```markdown
## Project Health Report

**Date**: YYYY-MM-DD HH:MM
**Overall Status**: 🟢 Healthy / 🟡 Warning / 🔴 Critical

### Code Quality
| Check | Status | Details |
|-------|--------|---------|
| Backend Lint (ruff) | ✅/❌ | X issues |
| Backend Types (pyrefly) | ✅/❌ | X errors |
| Frontend Lint (biome) | ✅/❌ | X issues |
| Frontend Types (tsc) | ✅/❌ | X errors |

### Tests
| Suite | Passed | Failed | Skipped |
|-------|--------|--------|---------|
| Backend Unit | X | X | X |
| Frontend Unit | X | X | X |
| Frontend E2E | X | X | X |

### Security
| Scan | Status | Findings |
|------|--------|----------|
| Trivy Backend | ✅/❌ | X HIGH, X CRITICAL |
| Trivy Frontend | ✅/❌ | X HIGH, X CRITICAL |
| Secret Detection | ✅/❌ | X findings |

### Dependencies
- Backend: X outdated packages
- Frontend: X outdated packages

### Docker
| Image | Build Status | Size |
|-------|-------------|------|
| Backend | ✅/❌ | X MB |
| Frontend | ✅/❌ | X MB |

### Recommendations
1. [Priority] Action item
2. [Priority] Action item
```
