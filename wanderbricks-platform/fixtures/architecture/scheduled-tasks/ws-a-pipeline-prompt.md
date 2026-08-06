# Scheduled Task Prompt — Workstream A: SDP Pipeline (Bronze → Silver → Gold)

## scheduleAgentTool Parameters

- **title:** `WanderBricks WS-A Pipeline`
- **cronExpression:** `0 */3 * * * ?` (first workstream — fast poll for immediate feedback)

## Instructions (copy verbatim into scheduleAgentTool)

```
You are executing Workstream A of the WanderBricks Platform: building the full Spark Declarative Pipeline (bronze → silver → gold).

Bundle root (ALL work here): /Workspace/Users/matthew.giglia@databricks.com/genieCodeWorkshop/wanderbricks-platform/
Push clone (git sync only): /Workspace/Users/matthew.giglia@databricks.com/genie-code-workstream-orchestration/genieCodeWorkshop/push-clone/
Git remote: https://github.com/mkgs-databricks-demos/genieCodeWorkshop.git
Branch name: mg-genie-wb-ws-a-pipeline
Upstream branch: mg-genie-L02-wanderbricks-scaffold

== GATE CHECK ==

1. Read /Workspace/Users/matthew.giglia@databricks.com/genieCodeWorkshop/wanderbricks-platform/fixtures/handoffs/workstream-a-status.md
2. Parse YAML frontmatter. If status is "COMPLETE": respond "WS-A already complete." and stop.
3. If status is "IN_PROGRESS": check if gold tables exist with rows. If yes, proceed to validation (step 10). If no, respond "WS-A in progress elsewhere. Exiting." and stop.

4. Read /Workspace/Users/matthew.giglia@databricks.com/genieCodeWorkshop/wanderbricks-platform/fixtures/handoffs/workstream-0-status.md
5. Parse YAML frontmatter. If status != "COMPLETE":
   - Respond "Upstream WS-0 not complete. Waiting." and stop.

6. Verify schema exists: SELECT 1 FROM information_schema.schemata WHERE catalog_name = 'hls_fde_dev' AND schema_name = 'dev_matthew_giglia_wanderbricks_ai'
   - If no rows: respond "Schema not deployed. Waiting." and stop.

== CONTEXT ==

Read these files from the bundle root:
- /Workspace/Users/matthew.giglia@databricks.com/genieCodeWorkshop/wanderbricks-platform/PROJECT_MEMORY.md
- /Workspace/Users/matthew.giglia@databricks.com/genieCodeWorkshop/wanderbricks-platform/fixtures/handoffs/workstream-0-status.md (read "Notes for Downstream Sessions")
- /Workspace/Users/matthew.giglia@databricks.com/genieCodeWorkshop/docs/reference/wanderbricks-analytics-handbook.md
- /Workspace/Users/matthew.giglia@databricks.com/genieCodeWorkshop/docs/conventions/genie-code-best-practices.md (section: Spark Declarative Pipeline Conventions)

Also explore the source data:
- SELECT * FROM samples.wanderbricks.properties LIMIT 5
- SELECT * FROM samples.wanderbricks.bookings LIMIT 5
- SELECT * FROM samples.wanderbricks.reviews LIMIT 5
- DESCRIBE TABLE samples.wanderbricks.customer_support_logs
- DESCRIBE TABLE samples.wanderbricks.clickstream

== EXECUTE ==

7. Set workstream-a-status.md to IN_PROGRESS with started_at timestamp.

8. SINGLE-FIRE GUARD: Deactivate your own cron immediately.
   List: GET alerts-internal/scheduled-insights-list/GENIE_CODE?parent_asset_name=users/{id}
   Find: display_name == "WanderBricks WS-A Pipeline"
   PATCH: alerts-internal/scheduled-insights/{auto_id} with body:
     {"scheduled_insight": {"name": <full_name>, "schedule": {"paused": true}},
      "etag": <etag>, "update_mask": "schedule.paused"}
   If fails, continue (IN_PROGRESS gate is backup).

9. WORKING DIRECTORY — ALL WORK IN BUNDLE ROOT:
   All code, resources, and config are created/edited via editAsset in the bundle root.
   All deploys use runDatabricksCli (bundle validate/deploy/run) in the bundle root.
   Do NOT run any runGit operations until the GIT SYNC step at the end.

9b. BUNDLE-FIRST RULE (CRITICAL):
    - ALL resources (pipelines, jobs, schemas, volumes) MUST be defined in
      resources/*.yml and deployed via `databricks bundle deploy --target dev`.
    - NEVER hardcode catalog/schema names. Use ${var.catalog}, ${var.schema},
      ${resources.schemas.wanderbricks_schema.catalog_name}, ${resources.schemas.wanderbricks_schema.name}.
    - NEVER create resources via SDK calls or raw SQL outside bundle deploy.
    - `databricks bundle validate --target dev` MUST pass before deploying.
    - A resource without the bundle dev prefix is INCORRECT even if it runs.

IMPORTANT: When in doubt about the best way to implement something, use your available
tools (docSearch, spark APIs, skill files) to check the latest Databricks best practices
before proceeding. Always prefer modern APIs and patterns.

10. Build the pipeline:

   TARGET SCHEMA: hls_fde_dev.dev_matthew_giglia_wanderbricks_ai
   SOURCE: samples.wanderbricks (all 16 tables)

   a. Create resource YAML: resources/wanderbricks_pipeline.pipeline.yml
      - Pipeline name: wanderbricks_pipeline
      - Serverless: true
      - Channel: PREVIEW
      - Edition: ADVANCED (needed for expectations)
      - Catalog: ${resources.schemas.wanderbricks_schema.catalog_name}
      - Schema: ${resources.schemas.wanderbricks_schema.name}
      - Libraries: include ../src/pipelines/**
      - Configuration:
        catalog_use: ${resources.schemas.wanderbricks_schema.catalog_name}
        schema_use: ${resources.schemas.wanderbricks_schema.name}

   b. Create src/pipelines/ directory with these notebooks:

      BRONZE LAYER (src/pipelines/bronze.py):
      - Streaming tables for core entities: properties, bookings, reviews, users, hosts, destinations, payments, countries, amenities, property_amenities, property_images
      - Each reads from samples.wanderbricks.{table} via spark.readStream.table()
      - Minimal transformation — add ingestion timestamp, preserve all source columns
      - Use @dp.table(name="bronze_{table}", comment="...")
      - Add basic expectations: @dp.expect("pk_not_null", "{pk_col} IS NOT NULL")

      SILVER LAYER (src/pipelines/silver.py):
      - Materialized views reading from bronze tables
      - Transformations:
        * Deduplicate on natural keys
        * Cast types (dates, numerics)
        * Handle nulls (default values for non-nullable business fields)
        * Standardize naming (snake_case)
        * Join dimension keys where needed
      - Key silver tables:
        * silver_properties (with destination_name joined)
        * silver_bookings (with duration_nights calculated, status standardized)
        * silver_reviews (with booking/property context joined)
        * silver_users, silver_hosts, silver_payments
      - Expectations: no null PKs, valid date ranges, positive amounts

      GOLD LAYER (src/pipelines/gold.py):
      - Materialized views for business aggregates:
        * gold_revenue_daily: daily GBV, net revenue, booking count by property/destination
        * gold_occupancy_monthly: occupancy rate, ADR, ALOS by property/destination/month
        * gold_guest_satisfaction: GSS per property (with recency weighting per Analytics Handbook)
        * gold_host_performance: superhost qualification metrics per host
        * gold_property_summary: denormalized property view with all key metrics
      - Follow Analytics Handbook definitions EXACTLY for all metric calculations
      - Use recency-weighted GSS formula (30d=3.0, 90d=2.0, 365d=1.0, >365d=0.5)

   c. Use modern SDP API throughout:
      ```python
      from pyspark import pipelines as dp
      @dp.table(name="...", comment="...")
      @dp.expect("...", "...")
      @dp.materialized_view(name="...", comment="...")
      spark.readStream.table("catalog.schema.table")
      spark.read.table("catalog.schema.table")
      ```

== VALIDATE ==

11. Run: databricks bundle validate --target dev (fix any errors)
12. Run: databricks bundle deploy --target dev
13. Trigger pipeline refresh: databricks bundle run wanderbricks_pipeline --target dev
14. Wait for pipeline completion
15. Run validation queries:
    * SELECT COUNT(*) FROM hls_fde_dev.dev_matthew_giglia_wanderbricks_ai.bronze_bookings
      (should match samples.wanderbricks.bookings count)
    * SELECT COUNT(*) FROM hls_fde_dev.dev_matthew_giglia_wanderbricks_ai.silver_bookings
      (should be <= bronze, no duplicates)
    * SELECT COUNT(*), SUM(gbv) FROM hls_fde_dev.dev_matthew_giglia_wanderbricks_ai.gold_revenue_daily
      (should have rows, positive GBV)
    * SELECT COUNT(DISTINCT property_id) FROM hls_fde_dev.dev_matthew_giglia_wanderbricks_ai.gold_occupancy_monthly
      (should cover multiple properties)
    * SELECT AVG(gss) FROM hls_fde_dev.dev_matthew_giglia_wanderbricks_ai.gold_guest_satisfaction
      (should be between 1.0 and 5.0)

== COMPLETE ==

16. Update fixtures/handoffs/workstream-a-status.md:
    - status: COMPLETE, completed_at, output_tables (list all bronze/silver/gold tables), validation: PASSED, bundle_deployed: true, tests_passed: true
    - "What Was Built" section describing the pipeline architecture
    - "Notes for Downstream Sessions":
      * Gold table names and key columns for metric views (WS-B)
      * Silver table names for feature engineering (WS-D)
      * How to query: fully qualified names
    - Write session summary to fixtures/sessions/ (date + description)
    - Update fixtures/sessions/INDEX.md

== GIT SYNC (one-way, end of session) ==

17. Ensure push clone exists:
    Path: /Workspace/Users/matthew.giglia@databricks.com/genie-code-workstream-orchestration/genieCodeWorkshop/push-clone/
    If NOT: runGit clone (url: https://github.com/mkgs-databricks-demos/genieCodeWorkshop.git, path: above, provider: gitHub)
18. In push clone: checkout mg-genie-L02-wanderbricks-scaffold, pull latest.
19. Create/checkout branch mg-genie-wb-ws-a-pipeline.
20. Copy YOUR files from bundle root → push clone (executeCode with file I/O):
    - wanderbricks-platform/resources/wanderbricks_pipeline.pipeline.yml
    - wanderbricks-platform/src/pipelines/bronze.py
    - wanderbricks-platform/src/pipelines/silver.py
    - wanderbricks-platform/src/pipelines/gold.py
    - wanderbricks-platform/fixtures/handoffs/workstream-a-status.md
    - wanderbricks-platform/fixtures/sessions/*.md (your session file)
21. Commit + push: runGit commit_and_push on the push clone.

IMPORTANT:
- Never commit to main or lesson branches directly.
- Use modern SDP API ONLY (from pyspark import pipelines as dp). Never import dlt.
- Use ${resources.schemas.wanderbricks_schema.*} for schema refs in resource YAML.
- Follow the Analytics Handbook definitions exactly for gold layer calculations.
- The push clone is WRITE-ONLY. Never read from it. Never edit files there directly.
```
