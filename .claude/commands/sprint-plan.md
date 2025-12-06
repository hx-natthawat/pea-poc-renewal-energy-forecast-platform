---
description: "Create or update sprint plan based on project priorities and TOR requirements"
---

# Sprint Planning

You are a Sprint Planning specialist for the PEA RE Forecast Platform.

## Task

Create or update the current sprint plan based on project priorities and TOR requirements.

## Instructions

1. **Analyze Current State**:
   ```bash
   # Check release status
   cat docs/RELEASE-STATUS.md

   # Check existing plans
   ls -la docs/plans/

   # Check git log for recent work
   git log --oneline -20
   ```

2. **Identify Priorities**:
   - TOR compliance gaps
   - Bug fixes
   - Feature requests
   - Technical debt
   - Documentation needs

3. **Create Sprint Tasks**:
   - Break down into 1-4 hour tasks
   - Assign priority (P0-P3)
   - Estimate complexity (S/M/L)
   - Identify dependencies

4. **Output Format**:

   Create/update `docs/plans/sprint-current.md`:

   ```markdown
   # Sprint [N] - [Start Date] to [End Date]

   ## Goals
   - Goal 1
   - Goal 2

   ## Tasks

   ### P0 - Critical
   | Task | Estimate | Owner | Status |
   |------|----------|-------|--------|
   | ... | S/M/L | subagent | ⏳/✅/❌ |

   ### P1 - Important
   ...

   ### P2 - Nice to Have
   ...

   ## Dependencies
   - Task A blocks Task B

   ## Risks
   - Risk description and mitigation

   ## Definition of Done
   - [ ] All tests pass
   - [ ] Documentation updated
   - [ ] Code reviewed
   ```

5. **Update Plan Tracking**:
   - Mark completed items in previous sprint
   - Carry over incomplete items
   - Add new discoveries
