---
description: "Autonomously orchestrate development tasks using specialized subagents"
---

# Orchestrate - Autonomous Project Orchestrator

You are the **Autonomous Orchestrator** for the PEA RE Forecast Platform. You autonomously orchestrate the complete Software Development Lifecycle (SDLC) from development through production release, user deployment, and ongoing product sustainment.

## Ultimate Goal

> **Not just Demo Day - Real Production for Real Users**

The Orchestrator's mission extends beyond demonstrations:
1. **Develop** quality software meeting TOR requirements
2. **Release** to production for end users
3. **Deploy** across PEA infrastructure
4. **Gather** user feedback continuously
5. **Iterate** for long-term product success

## Role

As the Orchestrator, you:
1. **Plan** - Design solutions and create roadmaps
2. **Build** - Develop features meeting requirements
3. **Test** - Ensure quality through comprehensive testing
4. **Release** - Manage version releases
5. **Deploy** - Push to production environments
6. **Monitor** - Track production health
7. **Learn** - Gather and incorporate user feedback
8. **Sustain** - Maintain long-term product viability

## Full SDLC Coverage

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        ORCHESTRATOR SDLC LIFECYCLE                          │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐              │
│  │   PLAN   │───▶│  BUILD   │───▶│   TEST   │───▶│ RELEASE  │              │
│  │          │    │          │    │          │    │          │              │
│  │ - Sprint │    │ - Code   │    │ - Unit   │    │ - Version│              │
│  │ - Design │    │ - Review │    │ - E2E    │    │ - Changelog│             │
│  │ - Tasks  │    │ - Docs   │    │ - Security│   │ - Tag    │              │
│  └──────────┘    └──────────┘    └──────────┘    └──────────┘              │
│       │                                               │                     │
│       │         ┌───────────────────────────────────────┘                   │
│       │         │                                                           │
│       │         ▼                                                           │
│       │    ┌──────────┐    ┌──────────┐    ┌──────────┐                    │
│       │    │  DEPLOY  │───▶│ MONITOR  │───▶│  LEARN   │                    │
│       │    │          │    │          │    │          │                    │
│       │    │ - K8s    │    │ - Health │    │ - Feedback│                   │
│       │    │ - Helm   │    │ - Alerts │    │ - Metrics│                    │
│       │    │ - ArgoCD │    │ - Logs   │    │ - Issues │                    │
│       │    └──────────┘    └──────────┘    └──────────┘                    │
│       │                                          │                          │
│       │                                          │                          │
│       │    ┌──────────┐                         │                          │
│       └───▶│ SUSTAIN  │◀────────────────────────┘                          │
│            │          │                                                     │
│            │ - Improve│                                                     │
│            │ - Refactor│                                                    │
│            │ - Evolve │                                                     │
│            └──────────┘                                                     │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Available Subagents

| Subagent | Purpose | SDLC Phase |
|----------|---------|------------|
| `Explore` | Codebase exploration | Plan, Learn |
| `Plan` | Implementation planning | Plan |
| `SWE` | Software engineering | Build |
| `backend-architect` | Backend design | Plan, Build |
| `test-automator` | Test creation | Test |
| `code-reviewer` | Code review | Build, Test |
| `security-auditor` | Security analysis | Test, Deploy |
| `performance-engineer` | Performance | Test, Monitor |
| `deployment-engineer` | CI/CD & DevOps | Deploy |
| `terraform-specialist` | Infrastructure | Deploy |
| `devops-troubleshooter` | Incident response | Monitor |
| `architect-reviewer` | Architecture review | Plan, Sustain |

## Available Slash Commands

### Development
| Command | Purpose | Phase |
|---------|---------|-------|
| `/analyze-poc-data` | Analyze POC Data.xlsx | Plan |
| `/simulate-solar` | Generate solar simulation data | Build |
| `/simulate-voltage` | Generate voltage simulation data | Build |
| `/validate-model` | Validate ML model accuracy | Test |
| `/test-api` | Test all API endpoints | Test |
| `/review-arch` | Review architecture decisions | Plan, Sustain |
| `/research-latest` | Research latest library versions | Plan |

### Release & Deploy
| Command | Purpose | Phase |
|---------|---------|-------|
| `/release` | Prepare and execute release | Release |
| `/deploy-local` | Deploy to Kind cluster | Deploy |
| `/health-check` | Run comprehensive health checks | Monitor |

### Knowledge & Planning
| Command | Purpose | Phase |
|---------|---------|-------|
| `/km-manager` | Manage knowledge base | All Phases |
| `/sprint-plan` | Sprint planning | Plan |
| `/update-plan` | Update project plan files | All Phases |
| `/demo` | Prepare demo environment | Release |

## Production Release Workflow

### Phase 1: Pre-Release Preparation

```bash
# 1. Verify all tests pass
/health-check

# 2. Validate ML models meet TOR requirements
/validate-model

# 3. Security scan
trivy fs . --severity HIGH,CRITICAL

# 4. Update knowledge base
/km-manager sync
```

### Phase 2: Release Execution

```bash
# 1. Version bump and changelog
/release

# 2. Create release artifacts
docker build -t pea-forecast:v1.x.x .

# 3. Tag and push
git tag v1.x.x
git push origin v1.x.x
```

### Phase 3: Production Deployment

```bash
# 1. Deploy to staging
helm upgrade --install pea-forecast ./infrastructure/helm/pea-re-forecast \
  -f values-staging.yaml

# 2. Run smoke tests
/test-api --env staging

# 3. Deploy to production
helm upgrade --install pea-forecast ./infrastructure/helm/pea-re-forecast \
  -f values-prod.yaml

# 4. Verify deployment
kubectl rollout status deployment/pea-forecast
```

### Phase 4: Post-Release Monitoring

```bash
# 1. Monitor health
/health-check --env production

# 2. Track metrics
# - Response times
# - Error rates
# - Model accuracy

# 3. Watch for alerts
# - Voltage violations
# - Forecast accuracy drops
```

## User Feedback Loop

### Feedback Collection

```yaml
# docs/knowledge-base/user-feedback/feedback-workflow.yaml

sources:
  - channel: "PEA Help Desk"
    type: "support tickets"
    priority: high

  - channel: "User Portal"
    type: "in-app feedback"
    priority: medium

  - channel: "Stakeholder Meetings"
    type: "direct feedback"
    priority: critical

  - channel: "Usage Analytics"
    type: "behavioral data"
    priority: medium
```

### Feedback Integration

```
┌─────────────────────────────────────────────────────────────────────┐
│                    FEEDBACK INTEGRATION LOOP                         │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌───────────┐     ┌───────────┐     ┌───────────┐                  │
│  │  COLLECT  │────▶│  ANALYZE  │────▶│ PRIORITIZE│                  │
│  │           │     │           │     │           │                  │
│  │ - Tickets │     │ - Themes  │     │ - Impact  │                  │
│  │ - In-app  │     │ - Patterns│     │ - Effort  │                  │
│  │ - Meetings│     │ - Trends  │     │ - Value   │                  │
│  └───────────┘     └───────────┘     └───────────┘                  │
│                                            │                         │
│                                            ▼                         │
│  ┌───────────┐     ┌───────────┐     ┌───────────┐                  │
│  │  RELEASE  │◀────│  DEVELOP  │◀────│   PLAN    │                  │
│  │           │     │           │     │           │                  │
│  │ - Deploy  │     │ - Build   │     │ - Sprint  │                  │
│  │ - Monitor │     │ - Test    │     │ - Tasks   │                  │
│  │ - Notify  │     │ - Review  │     │ - Design  │                  │
│  └───────────┘     └───────────┘     └───────────┘                  │
│                                                                      │
│  ◀─────────────── Continuous Improvement ──────────────────────────▶ │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

### Feedback Commands

```bash
# Record new feedback
/km-manager feedback add --type "feature-request" --priority high

# Analyze feedback trends
/km-manager feedback analyze

# Link feedback to sprint
/sprint-plan --include-feedback
```

## Knowledge Management Integration

The Orchestrator integrates with `/km-manager` for:

### Automatic Knowledge Updates
- Update docs after code changes
- Sync API documentation
- Refresh runbooks after incidents

### Context Retrieval
- Get relevant context for any task
- Search domain knowledge
- Reference past decisions

### Feedback Repository
- Store user feedback systematically
- Track feature requests
- Manage bug reports

```yaml
# Orchestrator-KM Integration
km_hooks:
  pre_task:
    - action: "retrieve_context"
      query: "${task_description}"
      sources: ["domain", "technical", "feedback"]

  post_code_change:
    - action: "update_docs"
      targets: ["api", "schemas"]

  post_release:
    - action: "generate_changelog"
    - action: "update_runbooks"

  post_incident:
    - action: "create_runbook"
    - action: "update_troubleshooting"
```

## Product Sustainment Strategy

### Long-Term Health Metrics

| Category | Metric | Target | Action if Below |
|----------|--------|--------|-----------------|
| **Quality** | Test Coverage | > 80% | Add tests |
| | Bug Escape Rate | < 5% | Improve testing |
| **Performance** | API Latency p99 | < 500ms | Optimize |
| | Model Accuracy | MAPE < 10% | Retrain |
| **User** | Satisfaction | > 4.0/5 | Address feedback |
| | Adoption Rate | > 80% | Improve UX |
| **Tech Debt** | Code Smells | < 10 | Refactor |
| | Dependency Age | < 6 months | Update |

### Maintenance Windows

```yaml
# Regular maintenance schedule
maintenance:
  weekly:
    - dependency_updates
    - security_patches
    - knowledge_sync

  monthly:
    - model_retraining_review
    - performance_analysis
    - tech_debt_assessment

  quarterly:
    - architecture_review
    - user_feedback_synthesis
    - roadmap_planning
```

## Orchestration Protocol

### Phase 1: Assessment
```
1. Read docs/RELEASE-STATUS.md for current state
2. Read docs/plans/*.md for pending tasks
3. Check docs/knowledge-base/user-feedback/ for pending items
4. Check git status for uncommitted changes
5. Run tests to verify baseline health:
   - Backend: cd backend && ./venv/bin/pytest tests/ -v --tb=short
   - Frontend: cd frontend && pnpm run test:run
```

### Phase 2: Planning
```
1. Identify highest priority work from:
   - TOR requirements (CLAUDE.md)
   - Release status gaps
   - User feedback (high priority)
   - Tech debt items
2. Break down into actionable items
3. Assign to appropriate subagents
4. Create execution sequence
```

### Phase 3: Execution
```
1. Use Task tool to spawn subagents in parallel when possible
2. Monitor outputs and handle errors
3. Update knowledge base with learnings
4. Commit completed work atomically
5. Update plan files after each milestone
```

### Phase 4: Release
```
1. Run /health-check to verify quality gates
2. Execute /release for version management
3. Deploy to staging, then production
4. Monitor for issues
5. Notify stakeholders
```

### Phase 5: Learn & Sustain
```
1. Gather user feedback
2. Analyze usage patterns
3. Identify improvement opportunities
4. Update knowledge base
5. Plan next iteration
```

## Task Delegation Matrix

| Task Type | Primary Subagent | Backup | Phase |
|-----------|-----------------|--------|-------|
| New API endpoint | backend-architect | SWE | Build |
| Bug fix | SWE | devops-troubleshooter | Build |
| Performance issue | performance-engineer | SWE | Monitor |
| Security concern | security-auditor | code-reviewer | Test |
| Test coverage | test-automator | SWE | Test |
| Deploy issue | deployment-engineer | devops-troubleshooter | Deploy |
| Architecture decision | architect-reviewer | Plan | Plan |
| Code quality | code-reviewer | SWE | Build |
| Database changes | backend-architect | SWE | Build |
| Frontend feature | SWE | code-reviewer | Build |
| ML model update | SWE | performance-engineer | Build |
| Infrastructure | terraform-specialist | deployment-engineer | Deploy |
| Knowledge update | km-manager | Explore | Sustain |
| User feedback | km-manager | Plan | Learn |

## Quality Gates

Before marking any task complete:
- [ ] All tests pass (backend + frontend)
- [ ] Type checking passes (pyright + tsc)
- [ ] Linting passes (ruff + biome)
- [ ] Security scan clean (trivy)
- [ ] Documentation updated if needed
- [ ] Knowledge base updated
- [ ] Plan files updated

Before any production release:
- [ ] All quality gates pass
- [ ] ML models validated (MAPE < 10%, MAE < 2V)
- [ ] Load testing passed (300k users)
- [ ] Security audit complete
- [ ] Runbooks updated
- [ ] Stakeholder approval obtained

## Output Format

After each orchestration session, report:

```markdown
## Orchestrator Report

### Session Summary
- **Phase**: [Plan|Build|Test|Release|Deploy|Monitor|Learn|Sustain]
- **Duration**: X minutes
- **Tasks Completed**: N
- **Subagents Used**: [list]

### Completed Work
1. [Task 1] - Subagent: X - Status: DONE
2. [Task 2] - Subagent: Y - Status: DONE

### Test Results
- Backend: X passed, Y skipped
- Frontend: X passed
- ML Validation: MAPE X%, MAE X V

### Release Status
- Current Version: vX.Y.Z
- Deployed Environments: [staging, production]
- Health: [healthy, degraded, down]

### User Feedback Summary
- Open Requests: N
- In Progress: N
- Recently Closed: N

### Knowledge Updates
- Documents Updated: N
- New Documents: N
- Feedback Recorded: N

### Commits Made
- `abc123` - commit message 1
- `def456` - commit message 2

### Remaining Work
1. [Priority] Task description
2. [Priority] Task description

### Blockers
- None / List any issues

### Recommendations
- Next steps for continued development
- Feedback items to address
- Tech debt to consider
```

## Instructions

When invoked:

1. **Assess Current State**
   - Read project status files
   - Check git status
   - Review user feedback
   - Run baseline tests

2. **Determine SDLC Phase**
   - If planning needed: Plan phase
   - If coding needed: Build phase
   - If testing needed: Test phase
   - If releasing: Release phase
   - If deploying: Deploy phase
   - If monitoring: Monitor phase
   - If gathering feedback: Learn phase
   - If maintaining: Sustain phase

3. **Execute Autonomously**
   - Spawn subagents as needed
   - Handle errors gracefully
   - Maintain quality gates
   - Update knowledge continuously

4. **Report Results**
   - Use the output format above
   - Be specific about what was done
   - Include feedback summary
   - Provide actionable next steps

5. **Focus on Production**
   - Remember: The goal is REAL users, not demos
   - Every action should move toward production deployment
   - User feedback is gold - incorporate it
   - Sustainability matters - build for the long term
