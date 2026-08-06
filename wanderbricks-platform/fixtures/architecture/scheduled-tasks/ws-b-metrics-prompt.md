# Scheduled Task Prompt — Workstream B: Metric Views + Orchestration Job

## scheduleAgentTool Parameters

- **title:** `WanderBricks WS-B Metrics`
- **cronExpression:** `0 */15 * * * ?`

## Instructions (copy verbatim into scheduleAgentTool)

```
You are executing Workstream B of the WanderBricks Platform: creating metric views and an orchestration job.

Project: /Users/matthew.giglia@databricks.com/genieCodeWorkshop/wanderbricks-platform/
Git repo: /Users/matthew.giglia@databricks.com/genieCodeWorkshop

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

Read these files:
- /Users/matthew.giglia@databricks.com/genieCodeWorkshop/wanderbricks-platform/PROJECT_MEMORY.md
- /Users/matthew.giglia@databricks.com/genieCodeWorkshop/wanderbricks-platform/fixtures/handoffs/workstream-a-status.md (read "Notes for Downstream Sessions" for gold table details)
- /Users/matthew.giglia@databricks.com/genieCodeWorkshop/docs/reference/wanderbricks-analytics-handbook.md (THIS IS YOUR PRIMARY REFERENCE — all metric definitions must match exactly)

== EXECUTE ==

7. Update workstream-b-status.md to status: IN_PROGRESS, set started_at.

8. Create git branch: mg-genie-wb-ws-b-metrics (from lesson/02-vibe-infra).

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
