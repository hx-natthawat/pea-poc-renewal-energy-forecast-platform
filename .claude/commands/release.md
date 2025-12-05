# Release Management

You are a Release Manager for the PEA RE Forecast Platform.

## Task

Prepare and execute a release following the release checklist.

## Pre-Release Checklist

### 1. Version Bump
```bash
# Check current version
grep version backend/pyproject.toml
grep version frontend/package.json

# Update versions (semantic versioning)
# MAJOR.MINOR.PATCH
```

### 2. Changelog Update
```bash
# Generate changelog from commits
git log --oneline $(git describe --tags --abbrev=0)..HEAD

# Update CHANGELOG.md with:
# - New features
# - Bug fixes
# - Breaking changes
# - Security updates
```

### 3. Quality Gates

Run all checks:
```bash
# Backend
cd backend
./venv/bin/ruff check app/
./venv/bin/pyrefly check
PYTHONPATH=. ./venv/bin/pytest tests/ -v

# Frontend
cd frontend
pnpm run check
pnpm run type-check
pnpm run test:run
```

### 4. Security Scan
```bash
# Full security scan
trivy fs . --severity HIGH,CRITICAL --exit-code 1
```

### 5. Documentation
- [ ] API docs updated (if API changed)
- [ ] README updated (if needed)
- [ ] DEPLOYMENT.md current
- [ ] RELEASE-STATUS.md updated

### 6. Release Steps

```bash
# 1. Create release branch
git checkout -b release/vX.Y.Z

# 2. Update version numbers
# backend/pyproject.toml
# frontend/package.json
# docs/RELEASE-STATUS.md

# 3. Commit version bump
git add -A
git commit -m "chore: bump version to vX.Y.Z"

# 4. Create tag
git tag -a vX.Y.Z -m "Release vX.Y.Z"

# 5. Push
git push origin release/vX.Y.Z
git push origin vX.Y.Z

# 6. Create PR to main
gh pr create --title "Release vX.Y.Z" --body "## Release Notes\n\n..."

# 7. After merge, create GitHub release
gh release create vX.Y.Z --title "vX.Y.Z" --notes-file CHANGELOG.md
```

### 7. Post-Release
- [ ] Verify CI/CD pipeline
- [ ] Monitor staging deployment
- [ ] Notify stakeholders
- [ ] Update project board

## Output

Update `docs/RELEASE-STATUS.md` with new version info.
