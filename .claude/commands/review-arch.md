# Review Architecture

You are a solutions architect reviewing the PEA RE Forecast Platform.

## Task
Review architecture decisions against TOR requirements and best practices.

## Review Checklist

### TOR Compliance (Section 7.1)

- [ ] **7.1.1** Hardware resources match Table 1 specifications
- [ ] **7.1.3** All software from Table 2 is used correctly
- [ ] **7.1.4** CI/CD with GitLab + ArgoCD implemented
- [ ] **7.1.5** All software is open-source or properly licensed
- [ ] **7.1.6** Audit logs and security logging implemented
- [ ] **7.1.7** Scalability for 2,000 plants + 300,000 consumers

### Architecture Principles

- [ ] **Separation of Concerns**: Clear boundaries between layers
- [ ] **Scalability**: Horizontal scaling capability
- [ ] **Resilience**: Fault tolerance and recovery
- [ ] **Security**: Defense in depth
- [ ] **Observability**: Metrics, logs, traces

### Technology Decisions

| Component | Decision | Rationale | Risk |
|-----------|----------|-----------|------|
| Database | TimescaleDB | Time-series optimized | Medium |
| Cache | Redis | Fast, TOR required | Low |
| Backend | FastAPI | Async, modern | Low |
| ML | XGBoost + TensorFlow | Proven accuracy | Medium |

## Instructions

1. **Document Review**:
   - Read current architecture in `docs/architecture/`
   - Cross-reference with CLAUDE.md specifications
   - Check TOR requirements

2. **Code Review**:
   - Review project structure
   - Check for anti-patterns
   - Verify security practices

3. **Scalability Analysis**:
   - Estimate load for 2,000 plants
   - Estimate storage for 300,000 consumers
   - Identify bottlenecks

4. **Output**:
   - Architecture Decision Records at `docs/architecture/adr/`
   - Review report at `docs/specs/architecture-review.md`
   - Action items in `docs/plans/architecture-improvements.md`

## ADR Template

```markdown
# ADR-XXX: [Title]

## Status
[Proposed | Accepted | Deprecated | Superseded]

## Context
[Why is this decision needed?]

## Decision
[What is the decision?]

## Consequences
[What are the results?]
```
