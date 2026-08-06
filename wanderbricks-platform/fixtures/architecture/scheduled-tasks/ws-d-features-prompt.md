# Scheduled Task Prompt — Workstream D: Feature Tables

## scheduleAgentTool Parameters

- **title:** `WanderBricks WS-D Features`
- **cronExpression:** `0 */15 * * * ?`

## Instructions (copy verbatim into scheduleAgentTool)

```
You are executing Workstream D of the WanderBricks Platform: creating feature tables for ML use cases.

Bundle root (ALL work here): /Workspace/Users/matthew.giglia@databricks.com/genieCodeWorkshop/wanderbricks-platform/
Push clone (git sync only): /Workspace/Users/matthew.giglia@databricks.com/genie-code-workstream-orchestration/genieCodeWorkshop/push-clone/
Git remote: https://github.com/mkgs-databricks-demos/genieCodeWorkshop.git
Branch name: mg-genie-wb-ws-d-features
Upstream branch: mg-genie-wb-ws-a-pipeline

== GATE CHECK ==

1. Read /Workspace/Users/matthew.giglia@databricks.com/genieCodeWorkshop/wanderbricks-platform/fixtures/handoffs/workstream-d-status.md
2. If status is "COMPLETE": respond "WS-D already complete." and stop.
3. If status is "IN_PROGRESS": respond "WS-D in progress elsewhere. Exiting." and stop.

4. Read /Workspace/Users/matthew.giglia@databricks.com/genieCodeWorkshop/wanderbricks-platform/fixtures/handoffs/workstream-a-status.md
5. If status != "COMPLETE": respond "Upstream WS-A not complete. Waiting." and stop.

6. Verify silver tables exist:
   SELECT COUNT(*) FROM hls_fde_dev.dev_matthew_giglia_wanderbricks_ai.silver_bookings
   - If doesn\'t exist or 0 rows: respond "Silver tables not populated. Waiting." and stop.

== CONTEXT ==

Read these files:
- /Workspace/Users/matthew.giglia@databricks.com/genieCodeWorkshop/wanderbricks-platform/PROJECT_MEMORY.md
- /Workspace/Users/matthew.giglia@databricks.com/genieCodeWorkshop/wanderbricks-platform/fixtures/handoffs/workstream-a-status.md ("Notes for Downstream Sessions")
- /Workspace/Users/matthew.giglia@databricks.com/genieCodeWorkshop/docs/reference/wanderbricks-analytics-handbook.md (feature definitions)

== EXECUTE ==

7. Set workstream-d-status.md to IN_PROGRESS with started_at.

8. SINGLE-FIRE GUARD: Self-pause via alerts-internal API (same pattern as other workstreams).

9. WORKING DIRECTORY — ALL WORK IN BUNDLE ROOT.
   Do NOT run any runGit operations until GIT SYNC at the end.

9b. BUNDLE-FIRST RULE: All resources in YAML, no hardcoded names, validate before deploy.

10. Create feature tables:

    a. Create src/features/ directory.

    b. Create src/features/host_performance_features.py:
       - Use FeatureEngineeringClient or Feature Views
       - Features: avg_rating_90d, completed_bookings_90d, cancellation_rate,
         response_rate, is_superhost, superhost_score
       - Source: silver_bookings, silver_reviews, silver_hosts

    c. Create src/features/property_quality_features.py:
       - Features: avg_rating, review_count, recent_gss, occupancy_rate_30d,
         price_percentile, quality_tier
       - Source: silver_properties, silver_bookings, silver_reviews

    d. Create resources/wanderbricks_features.yml:
       - Feature table definitions
       - Compute notebook paths

    e. Deploy: databricks bundle validate + deploy --target dev

== VALIDATE ==

11. Verify feature tables are created and populated.
12. Check feature count and value ranges.

== COMPLETE ==

13. Update fixtures/handoffs/workstream-d-status.md: COMPLETE with output details.

== GIT SYNC (one-way, end of session) ==

14. Ensure push clone exists (runGit clone if needed).
15. In push clone: checkout mg-genie-wb-ws-a-pipeline, pull latest.
16. Create/checkout branch mg-genie-wb-ws-d-features.
17. Copy YOUR files: src/features/*, resources/wanderbricks_features.yml, status file, session file.
18. Commit + push from push clone.

IMPORTANT: Never commit to main or lesson branches. Push clone is WRITE-ONLY.
```
