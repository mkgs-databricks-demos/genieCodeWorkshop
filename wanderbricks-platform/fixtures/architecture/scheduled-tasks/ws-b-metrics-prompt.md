# Scheduled Task Prompt — Workstream B: Metric Views + Orchestration Job

## scheduleAgentTool Parameters

- **title:** `WanderBricks WS-B Metrics`
- **cronExpression:** `0 */15 * * * ?`

## Instructions (copy verbatim into scheduleAgentTool)

```
You are executing Workstream B of the WanderBricks Platform: creating metric views and an orchestration job.

Bundle root (ALL work here): /Workspace/Users/matthew.giglia@databricks.com/genieCodeWorkshop/wanderbricks-platform/
Push clone (git sync only): /Workspace/Users/matthew.giglia@databricks.com/genie-code-workstream-orchestration/genieCodeWorkshop/push-clone/
Git remote: https://github.com/mkgs-databricks-demos/genieCodeWorkshop.git
Branch name: mg-genie-wb-ws-b-metrics
Upstream branch: mg-genie-wb-ws-a-pipeline

== GATE CHECK ==

1. Read /Workspace/Users/matthew.giglia@databricks.com/genieCodeWorkshop/wanderbricks-platform/fixtures/handoffs/workstream-b-status.md
2. Parse YAML frontmatter. If status is "COMPLETE": respond "WS-B already complete." and stop.
3. If status is "IN_PROGRESS": respond "WS-B in progress elsewhere. Exiting." and stop.

4. Read /Workspace/Users/matthew.giglia@databricks.com/genieCodeWorkshop/wanderbricks-platform/fixtures/handoffs/workstream-a-status.md
5. Parse YAML frontmatter. If status != "COMPLETE":
   - Respond "Upstream WS-A not complete. Waiting." and stop.

6. Verify gold tables exist:
   SELECT COUNT(*) FROM hls_fde_dev.dev_matthew_giglia_wanderbricks_ai.gold_revenue_daily
   - If table doesn\'t exist or has 0 rows: respond "Gold tables not populated. Waiting." and stop.

== CONTEXT ==

Read these files from the bundle root:
- /Workspace/Users/matthew.giglia@databricks.com/genieCodeWorkshop/wanderbricks-platform/PROJECT_MEMORY.md
- /Workspace/Users/matthew.giglia@databricks.com/genieCodeWorkshop/wanderbricks-platform/fixtures/handoffs/workstream-a-status.md (read "Notes for Downstream Sessions" for gold table details)
- /Workspace/Users/matthew.giglia@databricks.com/genieCodeWorkshop/docs/reference/wanderbricks-analytics-handbook.md (PRIMARY REFERENCE — all metric definitions must match exactly)

== EXECUTE ==

7. Set workstream-b-status.md to IN_PROGRESS with started_at timestamp.

8. SINGLE-FIRE GUARD: Deactivate your own cron immediately.
   List: GET alerts-internal/scheduled-insights-list/GENIE_CODE?parent_asset_name=users/{id}
   Find: display_name == "WanderBricks WS-B Metrics"
   PATCH: alerts-internal/scheduled-insights/{auto_id} with body:
     {"scheduled_insight": {"name": <full_name>, "schedule": {"paused": true}},
      "etag": <etag>, "update_mask": "schedule.paused"}
   If fails, continue (IN_PROGRESS gate is backup).

9. WORKING DIRECTORY — ALL WORK IN BUNDLE ROOT:
   All code, resources, and config are created/edited via editAsset in the bundle root.
   All deploys use runDatabricksCli (bundle validate/deploy/run) in the bundle root.
   Do NOT run any runGit operations until the GIT SYNC step at the end.

9b. BUNDLE-FIRST RULE (CRITICAL):
    - ALL resources MUST be defined in resources/*.yml and deployed via bundle deploy.
    - NEVER hardcode catalog/schema names.
    - `databricks bundle validate --target dev` MUST pass before deploying.

IMPORTANT: When in doubt about the best way to implement something, use your available
tools (docSearch, spark APIs, skill files) to check the latest Databricks best practices
before proceeding.

10. Build metric views and orchestration job:

   a. Create src/sql/ directory for metric view SQL files.

   b. Create metric views (each as a SQL file with CREATE OR REPLACE MATERIALIZED VIEW):

      src/sql/mv_revenue_metrics.sql:
      - Gross Booking Value (GBV): SUM(total_amount) WHERE status = \'confirmed\'
      - Net Revenue: GBV × 0.15
      - Average Daily Rate (ADR): SUM(total_amount) / SUM(duration_nights)
      - Grain: daily by property_id, destination_id

      src/sql/mv_occupancy_metrics.sql:
      - Occupancy Rate: booked_nights / available_nights
      - Average Length of Stay (ALOS): AVG(duration_nights)
      - Booking Lead Time: DATEDIFF(check_in, DATE(created_at))
      - Grain: monthly by property_id, destination_id

      src/sql/mv_guest_satisfaction.sql:
      - Guest Satisfaction Score (GSS) with recency weighting:
        * 30 days: weight=3.0, 90 days: weight=2.0, 365 days: weight=1.0, >365 days: weight=0.5
      - GSS = SUM(rating × recency_weight) / SUM(recency_weight)
      - Grain: per property_id

      src/sql/mv_host_performance.sql:
      - Superhost qualification (ALL must be met):
        1. Average rating >= 4.5 (trailing 90 days)
        2. Completed bookings >= 10 (trailing 90 days)
        3. Cancellation rate < 2%
        4. Response rate >= 90%
      - Grain: per host_id

   c. Create resources/wanderbricks_orchestration.job.yml:
      - Job: "WanderBricks Pipeline Refresh"
      - Task 1: Trigger pipeline refresh (wanderbricks_pipeline)
      - Task 2: Refresh metric views (depends on task 1)

   IMPORTANT: Metric definitions in the Analytics Handbook are the SOURCE OF TRUTH.

== VALIDATE ==

11. Run: databricks bundle validate --target dev
12. Run: databricks bundle deploy --target dev
13. Execute metric view creation
14. Run validation queries (verify GBV, occupancy rate, GSS ranges)

== COMPLETE ==

15. Update fixtures/handoffs/workstream-b-status.md:
    - status: COMPLETE, completed_at, output_tables, validation: PASSED
    - "Notes for Downstream Sessions": metric view names for Genie Agent (WS-C)

== GIT SYNC (one-way, end of session) ==

16. Ensure push clone exists (runGit clone if needed).
17. In push clone: checkout mg-genie-wb-ws-a-pipeline, pull latest.
18. Create/checkout branch mg-genie-wb-ws-b-metrics.
19. Copy YOUR files: src/sql/*, resources/wanderbricks_metrics.yml, resources/wanderbricks_orchestration.job.yml, status file, session file.
20. Commit + push from push clone.

IMPORTANT: Never commit to main or lesson branches. Push clone is WRITE-ONLY.
```
