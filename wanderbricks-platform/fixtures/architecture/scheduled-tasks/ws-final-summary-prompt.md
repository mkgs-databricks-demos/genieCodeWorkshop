# Scheduled Task Prompt — Workstream FINAL: Summary + Merge Instructions

## scheduleAgentTool Parameters

- **title:** `WanderBricks WS-FINAL Summary`
- **cronExpression:** `0 */15 * * * ?`

## Instructions (copy verbatim into scheduleAgentTool)

```
You are executing the FINAL workstream of the WanderBricks Platform: summarizing all work and producing merge instructions.

Bundle root: /Workspace/Users/matthew.giglia@databricks.com/genieCodeWorkshop/wanderbricks-platform/

== GATE CHECK ==

1. Read /Workspace/Users/matthew.giglia@databricks.com/genieCodeWorkshop/wanderbricks-platform/fixtures/handoffs/workstream-final-status.md
2. If status is "COMPLETE": respond "WS-FINAL already complete." and stop.
3. If status is "IN_PROGRESS": respond "WS-FINAL in progress elsewhere. Exiting." and stop.

4. Read ALL workstream status files (a, b, c, d).
5. ALL must be "COMPLETE". If any are not: respond "Not all workstreams complete. Waiting." and stop.

== EXECUTE ==

6. Set workstream-final-status.md to IN_PROGRESS with started_at.

7. SINGLE-FIRE GUARD: Self-pause via alerts-internal API.

8. Write a comprehensive session summary to fixtures/sessions/:
   - What each workstream built
   - Total tables created (bronze, silver, gold, metric views, feature tables)
   - Validation results
   - Architecture diagram

9. Write merge instructions (PR titles, descriptions, merge order):
   1. mg-genie-wb-ws-a-pipeline → mg-genie-L02-wanderbricks-scaffold
   2. mg-genie-wb-ws-b-metrics → mg-genie-L02-wanderbricks-scaffold
   3. mg-genie-wb-ws-d-features → mg-genie-L02-wanderbricks-scaffold
   4. mg-genie-wb-ws-c-genie-agent → mg-genie-L02-wanderbricks-scaffold

10. Update workstream-final-status.md to COMPLETE.

NOTE: WS-FINAL does NOT produce code or deploy resources. It only writes documentation
via editAsset (which persists immediately). No git operations are needed — the summary
lives in the workspace layer and will be included in the human-triggered merge commit.

IMPORTANT: Never commit to main or lesson branches directly.
```
