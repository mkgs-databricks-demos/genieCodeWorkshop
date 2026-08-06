# Scheduled Task Prompt — Workstream C: Genie Agent (AI/BI Space)

## scheduleAgentTool Parameters

- **title:** `WanderBricks WS-C Genie Agent`
- **cronExpression:** `0 */15 * * * ?`

## Instructions (copy verbatim into scheduleAgentTool)

```
You are executing Workstream C of the WanderBricks Platform: creating a Genie AI/BI space over the gold/metric layer.

Bundle root (ALL work here): /Workspace/Users/matthew.giglia@databricks.com/genieCodeWorkshop/wanderbricks-platform/
Push clone (git sync only): /Workspace/Users/matthew.giglia@databricks.com/genie-code-workstream-orchestration/genieCodeWorkshop/push-clone/
Git remote: https://github.com/mkgs-databricks-demos/genieCodeWorkshop.git
Branch name: mg-genie-wb-ws-c-genie-agent
Upstream branch: mg-genie-wb-ws-b-metrics

== GATE CHECK ==

1. Read /Workspace/Users/matthew.giglia@databricks.com/genieCodeWorkshop/wanderbricks-platform/fixtures/handoffs/workstream-c-status.md
2. If status is "COMPLETE": respond "WS-C already complete." and stop.
3. If status is "IN_PROGRESS": respond "WS-C in progress elsewhere. Exiting." and stop.

4. Read /Workspace/Users/matthew.giglia@databricks.com/genieCodeWorkshop/wanderbricks-platform/fixtures/handoffs/workstream-b-status.md
5. If status != "COMPLETE": respond "Upstream WS-B not complete. Waiting." and stop.

6. Verify metric views exist:
   SELECT COUNT(*) FROM hls_fde_dev.dev_matthew_giglia_wanderbricks_ai.mv_revenue_metrics
   - If doesn\'t exist or 0 rows: respond "Metric views not populated. Waiting." and stop.

== CONTEXT ==

Read these files:
- /Workspace/Users/matthew.giglia@databricks.com/genieCodeWorkshop/wanderbricks-platform/PROJECT_MEMORY.md
- /Workspace/Users/matthew.giglia@databricks.com/genieCodeWorkshop/wanderbricks-platform/fixtures/handoffs/workstream-b-status.md ("Notes for Downstream Sessions")
- /Workspace/Users/matthew.giglia@databricks.com/genieCodeWorkshop/docs/reference/wanderbricks-analytics-handbook.md

== EXECUTE ==

7. Set workstream-c-status.md to IN_PROGRESS with started_at.

8. SINGLE-FIRE GUARD: Self-pause via alerts-internal API (same pattern as other workstreams).

9. WORKING DIRECTORY — ALL WORK IN BUNDLE ROOT.
   Do NOT run any runGit operations until GIT SYNC at the end.

9b. BUNDLE-FIRST RULE: All resources in YAML, no hardcoded names, validate before deploy.

10. Create the Genie AI/BI Space:

    a. Create resources/wanderbricks_genie.yml:
       - Genie space configuration pointing to gold tables and metric views
       - Include all gold_* tables and mv_* metric views
       - Add natural language instructions for the agent

    b. Add instructions for the Genie space:
       - Define sample questions users might ask
       - Describe each table/view purpose
       - Include metric calculation context from Analytics Handbook

    c. Deploy: databricks bundle validate + deploy --target dev

== VALIDATE ==

11. Verify the Genie space is accessible and can answer sample queries.

== COMPLETE ==

12. Update fixtures/handoffs/workstream-c-status.md: COMPLETE with output details.

== GIT SYNC (one-way, end of session) ==

13. Ensure push clone exists (runGit clone if needed).
14. In push clone: checkout mg-genie-wb-ws-b-metrics, pull latest.
15. Create/checkout branch mg-genie-wb-ws-c-genie-agent.
16. Copy YOUR files: resources/wanderbricks_genie.yml, status file, session file.
17. Commit + push from push clone.

IMPORTANT: Never commit to main or lesson branches. Push clone is WRITE-ONLY.
```
