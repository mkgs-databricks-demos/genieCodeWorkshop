# WS-FINAL Template

Every orchestration MUST include a WS-FINAL. Copy and customize.

---

```markdown
# Scheduled Task Prompt — Workstream FINAL: Summary & Merge Instructions

## scheduleAgentTool Parameters

- **title:** `<Project> WS-FINAL Summary`
- **cronExpression:** `0 */15 * * * ?`

## Instructions

You are executing the FINAL workstream of the <Project> orchestration:
summarizing all completed work and providing merge instructions.

Orchestration hub: <absolute path to project root>

### GATE CHECK

1. Read workstream-final-status.md. If COMPLETE, stop.
2. Read ALL other workstream status files.
3. If ANY status != COMPLETE, report which are pending and stop.

### CONTEXT

Read: PROJECT_MEMORY.md, scheduled-tasks README, all workstream status files.

### EXECUTE

1. Set own status to IN_PROGRESS.

2. Compile session summary from all status files. Write to fixtures/sessions/.

   Include these sections:

   a. EXECUTIVE SUMMARY:
      - Total workstreams, duration, resources created

   b. PER-WORKSTREAM RECAP (for each):
      - Branch name, what was built, key outputs, duration

   c. MERGE PLAN (primary deliverable):
      For each workstream in merge order:
      - Branch: <source> → <target>
      - Title: "feat(<scope>): <description>"
      - Description: [2-3 sentences from "What Was Built"]
      - Files changed: [key files/directories]
      - Note: merge dependency (e.g., "merge AFTER PR #1")

   d. POST-MERGE VALIDATION:
      1. Checkout target branch (all PRs merged)
      2. databricks bundle validate --target dev
      3. databricks bundle deploy --target dev
      4. Verify all tables populated
      5. Cut next lesson/feature branch from this state

   e. CLEANUP:
      - Scheduled task titles to pause
      - Clone paths that are now disposable

3. Update fixtures/sessions/INDEX.md.
4. Set own status to COMPLETE.
5. Commit and push documentation changes.
6. Present the merge plan to the user.

This workstream writes ONLY documentation. No code, no branches, no deployments.
```
