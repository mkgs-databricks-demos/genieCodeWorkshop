# Scheduled Task Prompt — Workstream A: SDP Pipeline (Bronze → Silver → Gold)

## scheduleAgentTool Parameters

- **title:** `WanderBricks WS-A Pipeline`
- **cronExpression:** `0 */15 * * * ?`

## Instructions (copy verbatim into scheduleAgentTool)

```
You are executing Workstream A of the WanderBricks Platform: building the full Spark Declarative Pipeline (bronze → silver → gold).

Project: /Users/matthew.giglia@databricks.com/genieCodeWorkshop/wanderbricks-platform/
Git repo: /Users/matthew.giglia@databricks.com/genieCodeWorkshop

== GATE CHECK ==

1. Read /Users/matthew.giglia@databricks.com/genieCodeWorkshop/wanderbricks-platform/fixtures/handoffs/workstream-a-status.md
2. Parse YAML frontmatter. If status is "COMPLETE": respond "WS-A already complete." and stop.
3. If status is "IN_PROGRESS": check if gold tables exist with rows. If yes, proceed to validation (step 10). If no, respond "WS-A in progress elsewhere. Exiting." and stop.

4. Read /Users/matthew.giglia@databricks.com/genieCodeWorkshop/wanderbricks-platform/fixtures/handoffs/workstream-0-status.md
5. Parse YAML frontmatter. If status != "COMPLETE":
   - Respond "Upstream WS-0 not complete. Waiting." and stop.

6. Verify schema exists: SELECT 1 FROM information_schema.schemata WHERE catalog_name = 'hls_fde_dev' AND schema_name = 'dev_matthew_giglia_wanderbricks_ai'
   - If no rows: respond "Schema not deployed. Waiting." and stop.

== CONTEXT ==

Read these files:
- /Users/matthew.giglia@databricks.com/genieCodeWorkshop/wanderbricks-platform/PROJECT_MEMORY.md
- /Users/matthew.giglia@databricks.com/genieCodeWorkshop/wanderbricks-platform/fixtures/handoffs/workstream-0-status.md (read "Notes for Downstream Sessions")
- /Users/matthew.giglia@databricks.com/genieCodeWorkshop/docs/reference/wanderbricks-analytics-handbook.md
- /Users/matthew.giglia@databricks.com/genieCodeWorkshop/docs/conventions/genie-code-best-practices.md (section: Spark Declarative Pipeline Conventions)

Also explore the source data:
- SELECT * FROM samples.wanderbricks.properties LIMIT 5
- SELECT * FROM samples.wanderbricks.bookings LIMIT 5
- SELECT * FROM samples.wanderbricks.reviews LIMIT 5
- DESCRIBE TABLE samples.wanderbricks.customer_support_logs
- DESCRIBE TABLE samples.wanderbricks.clickstream

== EXECUTE ==

7. Update workstream-a-status.md to status: IN_PROGRESS, set started_at.
   Use editAsset (workspace file API) to edit the status file. Do NOT use git for this.

7b. SINGLE-FIRE GUARD — Execute this exact Python code to pause your own schedule:

    from databricks.sdk import WorkspaceClient
    w = WorkspaceClient()
    me = w.current_user.me()
    resp = w.api_client.do("GET", "/api/2.0/alerts-internal/scheduled-insights-list/GENIE_CODE",
                           query={"parent_asset_name": f"users/{me.id}"})
    for task in resp.get("scheduled_insights", []):
        if task.get("display_name") == "WanderBricks WS-A Pipeline":
            auto_id = task["name"].split("/")[-1]
            w.api_client.do("PATCH", f"/api/2.0/alerts-internal/scheduled-insights/{auto_id}",
                           body={
                               "scheduled_insight": {"name": task["name"], "schedule": {"paused": True}},
                               "etag": task["etag"],
                               "update_mask": "schedule.paused"
                           })
            break

    If this fails, continue — the IN_PROGRESS gate check provides backup protection.

7c. GIT FOLDER ISOLATION — Critical rules you MUST follow:
    - The ORCHESTRATION HUB (/Users/matthew.giglia@databricks.com/genieCodeWorkshop/) is a SHARED
      git folder used by multiple workstreams. NEVER run runGit checkout, commit, push, or any
      branch-switching operation on it. Doing so breaks other workstreams.
    - Status files (fixtures/handoffs/workstream-*-status.md) are edited via editAsset tool
      using their workspace file IDs — they do NOT require git operations.
    - ALL git operations (clone, checkout, branch, commit, push) happen ONLY in your WORKING CLONE.
    - Before any runGit call, verify repoPath starts with:
      /Workspace/Users/matthew.giglia@databricks.com/genie-code-workstream-orchestration/
      If you are about to use the orchestration hub path for git, STOP. You are making an error.

8. SET UP WORKING CLONE:
   a. Check if working clone path exists:
      /Workspace/Users/matthew.giglia@databricks.com/genie-code-workstream-orchestration/genieCodeWorkshop/a-pipeline
   b. If NOT: Use runGit clone:
      - operation: clone
      - url: https://github.com/mkgs-databricks-demos/genieCodeWorkshop.git
      - path: /Workspace/Users/matthew.giglia@databricks.com/genie-code-workstream-orchestration/genieCodeWorkshop/a-pipeline
      - provider: gitHub
   c. In the CLONE (repoPath = clone path): checkout lesson/02-vibe-infra, pull latest.
   d. Create new branch mg-genie-wb-ws-a-pipeline from lesson/02-vibe-infra.
   e. If clone ALREADY EXISTS: checkout mg-genie-wb-ws-a-pipeline (resume prior run).
   f. ALL code edits happen via editAsset on files in the CLONE path.
   g. ALL git commits/pushes use repoPath = the CLONE path above. NEVER the orchestration hub.

9. Build the pipeline:

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

   c. Create fixtures/config/pipeline_config.yml:
      - Source catalog: samples
      - Source schema: wanderbricks
      - Tables list with PKs and business keys for each

   d. Use modern SDP API throughout:
      ```python
      from pyspark import pipelines as dp
      @dp.table(name="...", comment="...")
      @dp.expect("...", "...")  
      @dp.materialized_view(name="...", comment="...")
      spark.readStream.table("catalog.schema.table")
      spark.read.table("catalog.schema.table")
      ```

10. VALIDATE:
    - Run: databricks bundle validate --target dev (fix any errors)
    - Run: databricks bundle deploy --target dev
    - Trigger pipeline refresh: databricks bundle run wanderbricks_pipeline --target dev
    - Wait for pipeline completion
    - Run validation queries:
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

11. COMPLETE:
    - Update fixtures/handoffs/workstream-a-status.md:
      - status: COMPLETE, completed_at, output_tables (list all bronze/silver/gold tables), validation: PASSED, bundle_deployed: true, tests_passed: true
      - "What Was Built" section describing the pipeline architecture
      - "Notes for Downstream Sessions":
        * Gold table names and key columns for metric views (WS-B)
        * Silver table names for feature engineering (WS-D)
        * How to query: fully qualified names
    - Write session summary to fixtures/sessions/ (date + description)
    - Update fixtures/sessions/INDEX.md
    - Commit and push branch mg-genie-wb-ws-a-pipeline
    - Provide detailed next steps for human review

IMPORTANT:
- Never commit to main or lesson branches directly.
- Use modern SDP API ONLY (from pyspark import pipelines as dp). Never import dlt.
- Use ${resources.schemas.wanderbricks_schema.*} for schema refs in resource YAML.
- Follow the Analytics Handbook definitions exactly for gold layer calculations.
- Commit and push incrementally as each layer is completed (bronze first, then silver, then gold).
```
