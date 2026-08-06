# Scheduled Task Prompt — Workstream D: Feature Tables

## scheduleAgentTool Parameters

- **title:** `WanderBricks WS-D Features`
- **cronExpression:** `0 */15 * * * ?`

## Instructions (copy verbatim into scheduleAgentTool)

```
You are executing Workstream D of the WanderBricks Platform: creating feature tables for host and property quality scoring.

Orchestration hub (status files): /Users/matthew.giglia@databricks.com/genieCodeWorkshop/wanderbricks-platform/
Working clone: /Users/matthew.giglia@databricks.com/genie-code-workstream-orchestration/genieCodeWorkshop/d-features/
Git remote: (same repo as orchestration hub)
Branch from: mg-genie-wb-ws-a-pipeline (branch stacking — gives access to WS-A code, parallel with WS-B)

== GATE CHECK ==

1. Read /Users/matthew.giglia@databricks.com/genieCodeWorkshop/wanderbricks-platform/fixtures/handoffs/workstream-d-status.md
2. Parse YAML frontmatter. If status is "COMPLETE": respond "WS-D already complete." and stop.
3. If status is "IN_PROGRESS": check if feature tables exist. If yes, proceed to validation (step 9). If no, respond "WS-D in progress elsewhere. Exiting." and stop.

4. Read /Users/matthew.giglia@databricks.com/genieCodeWorkshop/wanderbricks-platform/fixtures/handoffs/workstream-a-status.md
5. Parse YAML frontmatter. If status != "COMPLETE":
   - Respond "Upstream WS-A not complete. Waiting." and stop.

6. Verify silver/gold tables exist:
   SELECT COUNT(*) FROM hls_fde_dev.dev_matthew_giglia_wanderbricks_ai.silver_bookings
   - If table doesn't exist or has 0 rows: respond "Silver tables not populated. Waiting." and stop.

== CONTEXT ==

Read these files:
- /Users/matthew.giglia@databricks.com/genieCodeWorkshop/wanderbricks-platform/PROJECT_MEMORY.md
- /Users/matthew.giglia@databricks.com/genieCodeWorkshop/wanderbricks-platform/fixtures/handoffs/workstream-a-status.md (read "Notes for Downstream Sessions" for table details)
- /Users/matthew.giglia@databricks.com/genieCodeWorkshop/docs/reference/wanderbricks-analytics-handbook.md (sections 4.1 Superhost Status, 3.1 GSS)

== EXECUTE ==

7. Update workstream-d-status.md (in ORCHESTRATION HUB) to status: IN_PROGRESS, set started_at.

8. SET UP WORKING CLONE:
   a. Check if the working clone path exists.
   b. If NOT: Clone the git repo to that path.
   c. In the clone: checkout mg-genie-wb-ws-a-pipeline (upstream), pull latest.
   d. Create new branch mg-genie-wb-ws-d-features from mg-genie-wb-ws-a-pipeline.
   e. If clone ALREADY EXISTS: checkout mg-genie-wb-ws-d-features (resume).
   f. ALL code work in this clone. Status files in orchestration hub.

9. Build feature tables:

   a. Create src/features/ directory.

   b. Create src/features/host_features.py:
      A notebook that computes host-level features using the Databricks Feature Engineering client.

      Feature table: feature_host_performance
      Primary key: host_id
      Timestamp key: computed_at (for point-in-time correctness)

      Features (all trailing 90 days unless noted):
      - avg_rating DOUBLE: average review rating across all host properties
      - total_completed_bookings INT: count of completed bookings
      - cancellation_rate DOUBLE: host-initiated cancellations / total bookings
      - response_rate DOUBLE: responded within 24h / total booking requests
      - is_superhost BOOLEAN: meets ALL 4 criteria from Analytics Handbook
      - superhost_score DOUBLE: composite score (0-1) combining all 4 metrics normalized
      - total_revenue DOUBLE: lifetime GBV across all properties
      - avg_occupancy_rate DOUBLE: average occupancy across all properties
      - property_count INT: number of active listings

      Use FeatureEngineeringClient:
      ```python
      from databricks.feature_engineering import FeatureEngineeringClient
      fe = FeatureEngineeringClient()
      fe.create_table(
          name="hls_fde_dev.dev_matthew_giglia_wanderbricks_ai.feature_host_performance",
          primary_keys=["host_id"],
          timestamp_keys=["computed_at"],
          df=host_features_df,
          description="Host performance features for superhost qualification and scoring"
      )
      ```

   c. Create src/features/property_features.py:
      Feature table: feature_property_quality
      Primary key: property_id
      Timestamp key: computed_at

      Features (trailing 90 days unless noted):
      - avg_rating DOUBLE: average review rating for this property
      - review_count INT: total reviews
      - gss DOUBLE: Guest Satisfaction Score (recency-weighted per Analytics Handbook)
      - occupancy_rate DOUBLE: booked nights / available nights
      - avg_daily_rate DOUBLE: revenue / booked nights
      - repeat_guest_rate DOUBLE: guests who booked this property >1 time / total guests
      - negative_review_rate DOUBLE: reviews with rating < 3.0 / total reviews
      - property_quality_score DOUBLE: composite normalized score (0-1)
      - booking_lead_time_avg DOUBLE: average days between booking and check-in
      - revenue_per_available_night DOUBLE: RevPAN for this property

   d. Create resources/wanderbricks_features.yml:
      - Define a job to compute features on schedule
      - Task 1: host_features notebook
      - Task 2: property_features notebook (can run parallel with task 1)

10. VALIDATE:
    - Run: databricks bundle validate --target dev
    - Run: databricks bundle deploy --target dev
    - Run the feature computation notebooks
    - Validation queries:
      * SELECT COUNT(*) FROM hls_fde_dev.dev_matthew_giglia_wanderbricks_ai.feature_host_performance
        (should have 1 row per host)
      * SELECT COUNT(*) FROM hls_fde_dev.dev_matthew_giglia_wanderbricks_ai.feature_property_quality
        (should have 1 row per property)
      * SELECT AVG(superhost_score), COUNT(*) FILTER (WHERE is_superhost) FROM feature_host_performance
        (score should be 0-1, some superhosts should exist)
      * SELECT AVG(property_quality_score), MIN(property_quality_score), MAX(property_quality_score) FROM feature_property_quality
        (should be 0-1 range)
      * Verify no nulls in feature columns for entities with sufficient history:
        SELECT COUNT(*) FROM feature_host_performance WHERE avg_rating IS NULL AND total_completed_bookings > 0
        (should be 0)

11. COMPLETE:
    - Update fixtures/handoffs/workstream-d-status.md:
      - status: COMPLETE, completed_at, output_tables, validation: PASSED
      - "What Was Built" section
      - "Notes for Downstream Sessions": feature table names, key columns, how to use with FeatureLookup
    - Write session summary to fixtures/sessions/
    - Commit and push branch

IMPORTANT: Never commit to main or lesson branches directly. Superhost criteria must match Analytics Handbook exactly (4.5+ rating, 10+ bookings, <2% cancellation, 90%+ response). Use FeatureEngineeringClient for table creation (not raw Delta writes).
```
