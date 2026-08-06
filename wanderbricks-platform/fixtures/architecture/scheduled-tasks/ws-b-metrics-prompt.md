# Scheduled Task Prompt — Workstream B: Metric Views + Orchestration Job

## scheduleAgentTool Parameters

- **title:** `WanderBricks WS-B Metrics`
- **cronExpression:** `0 */15 * * * ?`

## Instructions (copy verbatim into scheduleAgentTool)

```
You are executing Workstream B of the WanderBricks Platform: creating metric views and an orchestration job.

Orchestration hub (status files): /Users/matthew.giglia@databricks.com/genieCodeWorkshop/wanderbricks-platform/
Working clone: /Users/matthew.giglia@databricks.com/genie-code-workstream-orchestration/genieCodeWorkshop/b-metrics/
Git remote: (same repo as orchestration hub)
Branch from: mg-genie-wb-ws-a-pipeline (branch stacking — gives access to WS-A code)

== GATE CHECK ==

1. Read /Users/matthew.giglia@databricks.com/genieCodeWorkshop/wanderbricks-platform/fixtures/handoffs/workstream-b-status.md
2. Parse YAML frontmatter. If status is "COMPLETE": respond "WS-B already complete." and stop.
3. If status is "IN_PROGRESS": check if metric views exist. If yes, proceed to validation (step 9). If no, respond "WS-B in progress elsewhere. Exiting." and stop.

4. Read /Users/matthew.giglia@databricks.com/genieCodeWorkshop/wanderbricks-platform/fixtures/handoffs/workstream-a-status.md
5. Parse YAML frontmatter. If status != "COMPLETE":
   - Respond "Upstream WS-A not complete. Waiting." and stop.

6. Verify gold tables exist:
   SELECT COUNT(*) FROM hls_fde_dev.dev_matthew_giglia_wanderbricks_ai.gold_revenue_daily
   - If table doesn't exist or has 0 rows: respond "Gold tables not populated. Waiting." and stop.

== CONTEXT ==

Before starting work, review the current state of the source code in the working clone.
Read the README, existing resources/, and src/ structure to understand what the project
already has and where it is currently.

Read these files:
- /Users/matthew.giglia@databricks.com/genieCodeWorkshop/wanderbricks-platform/PROJECT_MEMORY.md
- /Users/matthew.giglia@databricks.com/genieCodeWorkshop/wanderbricks-platform/fixtures/handoffs/workstream-a-status.md (read "Notes for Downstream Sessions" for gold table details)
- /Users/matthew.giglia@databricks.com/genieCodeWorkshop/docs/reference/wanderbricks-analytics-handbook.md (THIS IS YOUR PRIMARY REFERENCE — all metric definitions must match exactly)

== EXECUTE ==

7. Update workstream-b-status.md to IN_PROGRESS, set started_at.
   Use workspace file tools only. Do NOT use git for status files.

7b. SINGLE-FIRE GUARD: Deactivate your own cron immediately.
    List: GET alerts-internal/scheduled-insights-list/GENIE_CODE?parent_asset_name=users/{id}
    Find: display_name == "WanderBricks WS-B Metrics"
    PATCH: alerts-internal/scheduled-insights/{auto_id} with body:
      {"scheduled_insight": {"name": <full_name>, "schedule": {"paused": true}},
       "etag": <etag>, "update_mask": "schedule.paused"}
    If fails, continue (IN_PROGRESS gate is backup).
7d. BUNDLE-FIRST RULE (CRITICAL):
    - ALL resources (pipelines, jobs, schemas, volumes) MUST be defined in
      resources/*.yml and deployed via `databricks bundle deploy --target dev`.
    - NEVER hardcode catalog/schema names. Use ${var.catalog}, ${var.schema},
      ${resources.schemas.wanderbricks_schema.catalog_name}, ${resources.schemas.wanderbricks_schema.name}.
    - NEVER create resources via SDK calls or raw SQL outside bundle deploy.
    - `databricks bundle validate --target dev` MUST pass before deploying.
    - A resource without the bundle dev prefix is INCORRECT even if it runs.


7c. GIT FOLDER ISOLATION (CRITICAL):
    - /Users/matthew.giglia@databricks.com/genieCodeWorkshop/ = SHARED git folder.
      NEVER run runGit checkout/commit/push on it.
    - Status files: use workspace file tools only (no git).
    - ALL git ops: ONLY in WORKING CLONE path below.
    - Guard: repoPath MUST start with /Workspace/.../genie-code-workstream-orchestration/

8. SET UP WORKING CLONE:
   Path: /Workspace/Users/matthew.giglia@databricks.com/genie-code-workstream-orchestration/genieCodeWorkshop/b-metrics
   a. If NOT exists: runGit clone (url: https://github.com/mkgs-databricks-demos/genieCodeWorkshop.git, path: above, provider: gitHub)
   b. In CLONE: checkout mg-genie-wb-ws-a-pipeline (upstream), pull latest.
   c. Create branch mg-genie-wb-ws-b-metrics.
   d. If EXISTS: checkout mg-genie-wb-ws-b-metrics (resume).
   e. ALL code/git work in clone. NEVER in orchestration hub.

IMPORTANT: When in doubt about the best way to implement something, use your available
tools (docSearch, spark APIs, skill files) to check the latest Databricks best practices
before proceeding. Always prefer modern APIs and patterns.

9. Build metric views and orchestration job:

   a. Create src/sql/ directory for metric view SQL files.

   b. Create metric views as SQL files (each creates a MATERIALIZED VIEW or uses CREATE OR REPLACE VIEW):

      src/sql/mv_revenue_metrics.sql:
      - Gross Booking Value (GBV): SUM(total_amount) WHERE status = 'confirmed'
      - Net Revenue: GBV × 0.15
      - Average Daily Rate (ADR): SUM(total_amount) / SUM(duration_nights) for confirmed+completed
      - Grain: daily by property_id, destination_id
      - Time dimension: created_at (booking creation, NOT check-in)

      src/sql/mv_occupancy_metrics.sql:
      - Occupancy Rate: booked_nights / available_nights
      - Average Length of Stay (ALOS): AVG(duration_nights) for confirmed+completed
      - Booking Lead Time: DATEDIFF(check_in, DATE(created_at))
      - Grain: monthly by property_id, destination_id

      src/sql/mv_guest_satisfaction.sql:
      - Guest Satisfaction Score (GSS) with recency weighting:
        * Reviews in last 30 days: weight = 3.0
        * Reviews in last 90 days: weight = 2.0
        * Reviews in last 365 days: weight = 1.0
        * Reviews older than 365 days: weight = 0.5
      - GSS = SUM(rating × recency_weight) / SUM(recency_weight)
      - Review Response Rate: COUNT(DISTINCT reviews.booking_id) / COUNT(DISTINCT bookings.booking_id)
      - Grain: per property_id

      src/sql/mv_host_performance.sql:
      - Superhost qualification (ALL must be met):
        1. Average rating ≥ 4.5 (trailing 90 days)
        2. Completed bookings ≥ 10 (trailing 90 days)
        3. Cancellation rate < 2%
        4. Response rate ≥ 90%
      - Grain: per host_id

   c. Create resources/wanderbricks_metrics.yml:
      - Define each metric view as a resource (if supported), OR
      - Create a notebook that executes the SQL DDL statements
      - Reference: catalog_name and schema from ${resources.schemas.wanderbricks_schema.*}

   d. Create resources/wanderbricks_orchestration.job.yml:
      - Job: "WanderBricks Pipeline Refresh"
      - Task 1: Trigger pipeline refresh (wanderbricks_pipeline)
      - Task 2: Refresh metric views (depends on task 1)
      - Schedule: daily (or on-demand for dev)

   IMPORTANT: The metric definitions in the Analytics Handbook are the SOURCE OF TRUTH.
   Do not deviate from them. If a gold table already computes a metric, the metric view
   should reference the gold table. If additional logic is needed, add it in the view.

10. VALIDATE:
    - Run: databricks bundle validate --target dev
    - Run: databricks bundle deploy --target dev
    - Execute metric view creation (run the SQL or notebook)
    - Run validation queries:
      * SELECT COUNT(*), SUM(gbv), SUM(net_revenue) FROM the revenue metric view
        (verify net_revenue = gbv * 0.15)
      * SELECT AVG(occupancy_rate) FROM occupancy view (should be 0 < x < 1)
      * SELECT AVG(gss) FROM satisfaction view (should be 1.0 to 5.0)
      * SELECT COUNT(*) FROM host_performance WHERE is_superhost = true
        (should be a subset of all hosts)

11. COMPLETE:
    - Update fixtures/handoffs/workstream-b-status.md:
      - status: COMPLETE, completed_at, output_tables (metric view names), validation: PASSED
      - "What Was Built" section
      - "Notes for Downstream Sessions":
        * Metric view names and key columns
        * Which views are best for the Genie Agent (WS-C)
        * Sample questions each view can answer
    - Write session summary to fixtures/sessions/
    - Update fixtures/sessions/INDEX.md
    - Commit and push branch

IMPORTANT: Never commit to main or lesson branches directly. Metric definitions must match the Analytics Handbook EXACTLY. Use ${resources.schemas.wanderbricks_schema.*} for all schema references.
```
