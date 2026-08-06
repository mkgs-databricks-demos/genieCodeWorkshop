# Scheduled Task Prompt — Workstream FINAL: Summary & Merge Instructions

## scheduleAgentTool Parameters

- **title:** `WanderBricks WS-FINAL Summary`
- **cronExpression:** `0 */15 * * * ?`

## Instructions

You are executing the FINAL workstream of the WanderBricks Platform orchestration:
summarizing all completed work and providing merge instructions for the human operator.

Orchestration hub: /Users/matthew.giglia@databricks.com/genieCodeWorkshop/wanderbricks-platform/
Git repo: /Users/matthew.giglia@databricks.com/genieCodeWorkshop

### GATE CHECK

1. Read workstream-final-status.md in fixtures/handoffs/. If COMPLETE, stop.
2. Read workstream-a-status.md, workstream-b-status.md, workstream-c-status.md, workstream-d-status.md.
3. If ANY upstream status != COMPLETE, report which are pending and stop.

### CONTEXT

Read these files:
- PROJECT_MEMORY.md
- fixtures/architecture/scheduled-tasks/README.md
- All four workstream status files ("What Was Built" and "Notes for Downstream" sections)

### EXECUTE

1. Set workstream-final-status.md to IN_PROGRESS with started_at timestamp.

2. Compile a session summary from all workstream status files.

3. Write session summary to fixtures/sessions/ (YYYY-MM-DD_workstream-orchestration-complete.md):

   **Include these sections:**

   a. EXECUTIVE SUMMARY:
      - Total workstreams, total duration, resources created

   b. PER-WORKSTREAM RECAP (for A, B, C, D):
      - Branch name, what was built, key outputs, duration

   c. MERGE PLAN (primary deliverable):

      PR #1: mg-genie-wb-ws-a-pipeline → lesson/02-vibe-infra
      Title: "feat(L02): Add WanderBricks SDP pipeline (bronze→silver→gold)"
      Description: [from WS-A status]

      PR #2: mg-genie-wb-ws-b-metrics → lesson/02-vibe-infra
      Title: "feat(L02): Add metric views and orchestration job"
      Note: Merge AFTER PR #1 (branch stacked on WS-A)

      PR #3: mg-genie-wb-ws-d-features → lesson/02-vibe-infra
      Title: "feat(L02): Add feature tables (host performance, property quality)"
      Note: Merge AFTER PR #1, can merge in parallel with PR #2

      PR #4: mg-genie-wb-ws-c-genie-agent → lesson/02-vibe-infra
      Title: "feat(L02): Add WanderBricks Intelligence Genie space"
      Note: Merge AFTER PR #2 (branch stacked on WS-B)

   d. POST-MERGE VALIDATION:
      1. Checkout lesson/02-vibe-infra
      2. databricks bundle validate --target dev
      3. databricks bundle deploy --target dev
      4. Trigger pipeline refresh, verify all tables
      5. Cut lesson/03-vibe-ai from this state

   e. CLEANUP:
      - List scheduled task titles to pause
      - Note that ~/genie-code-workstream-orchestration/genieCodeWorkshop/ is disposable

4. Update fixtures/sessions/INDEX.md.

5. Set workstream-final-status.md to COMPLETE.

6. Commit and push documentation changes.

7. Provide the merge plan to the user with clear next steps.

This workstream writes ONLY documentation. No code, no new branches, no deployments.
