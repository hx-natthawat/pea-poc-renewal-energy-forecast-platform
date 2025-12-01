# Update Project Plan

You are a project manager for the PEA RE Forecast Platform.

## Task
Update the project plan with completed tasks and current status.

## Instructions

1. **Read Current Plans**:
   - `docs/plans/poc-progress.md` - POC phase tracking
   - `docs/plans/development-roadmap.md` - Overall roadmap
   - `docs/plans/sprint-current.md` - Current sprint

2. **Update Task Status**:
   ```markdown
   ## Task: [Task Name]
   - Status: [TODO | IN_PROGRESS | BLOCKED | DONE]
   - Completed: [DATE] (if done)
   - Notes: [Any relevant notes]
   - Blockers: [If blocked, what's blocking]
   ```

3. **Calculate Progress**:
   - Count completed vs total tasks
   - Update progress percentage
   - Identify risks and blockers

4. **Generate Summary**:
   ```markdown
   # Weekly Progress Summary

   ## Completed This Week
   - [x] Task 1
   - [x] Task 2

   ## In Progress
   - [ ] Task 3 (70%)

   ## Blockers
   - Issue: [description]
     Action: [what's needed]

   ## Next Week Goals
   - [ ] Task 4
   - [ ] Task 5
   ```

5. **Output**:
   - Update all plan files
   - Create summary at `docs/plans/status-[DATE].md`

## Plan File Structure

```
docs/plans/
├── poc-progress.md          # POC phase tracking
├── development-roadmap.md   # Overall phases
├── sprint-current.md        # Current sprint tasks
├── sprint-backlog.md        # Backlog items
├── deployment-log.md        # Deployment history
└── status-YYYY-MM-DD.md     # Weekly status reports
```
