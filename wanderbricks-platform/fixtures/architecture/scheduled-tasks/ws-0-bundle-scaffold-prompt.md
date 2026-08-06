# Scheduled Task Prompt — Workstream 0: Bundle Scaffold

> **Status:** COMPLETE (retrospective — this documents what the prompt WOULD have been)

## scheduleAgentTool Parameters

- **title:** `WanderBricks WS-0 Scaffold`
- **cronExpression:** N/A (would have been `0 */15 * * * ?`)

## Instructions (what the prompt would have contained)

```
You are executing Workstream 0 of the WanderBricks Platform: Bundle Scaffold.

Project: /Users/matthew.giglia@databricks.com/genieCodeWorkshop/wanderbricks-platform/
Git repo: /Users/matthew.giglia@databricks.com/genieCodeWorkshop

== GATE CHECK ==

1. Read /Users/matthew.giglia@databricks.com/genieCodeWorkshop/wanderbricks-platform/fixtures/handoffs/workstream-0-status.md
2. Parse YAML frontmatter. If status is "COMPLETE": respond "WS-0 already complete." and stop.
3. No upstream dependencies — proceed immediately.

== CONTEXT ==

Read these files:
- /Users/matthew.giglia@databricks.com/genieCodeWorkshop/wanderbricks-platform/PROJECT_MEMORY.md
- /Users/matthew.giglia@databricks.com/genieCodeWorkshop/PROJECT_MEMORY.md
- /Users/matthew.giglia@databricks.com/genieCodeWorkshop/docs/conventions/genie-code-best-practices.md (sections: DAB Conventions, Schema References)

== EXECUTE ==

4. Update workstream-0-status.md to status: IN_PROGRESS, set started_at.

5. Create git branch: mg-genie-L02-wanderbricks-scaffold (from lesson/02-vibe-infra).

6. Build the bundle scaffold:

   a. Update databricks.yml:
      - Add `include: - resources/*.yml`
      - Add variables: warehouse_id (lookup: "Serverless Starter Warehouse"), lakebase_project_id
      - Set dev target: mode: development, catalog: hls_fde_dev, schema: wanderbricks_ai, lakebase_project_id: wanderbricks-ai

   b. Create resources/wanderbricks_schema.schema.yml:
      - Schema resource using ${var.catalog} and ${var.schema}
      - Comment: "WanderBricks Intelligence Platform - gold analytics, metric views, features, and AI search artifacts"

   c. Create resources/wanderbricks_volumes.volume.yml:
      - Managed volume "reference_docs" in the schema
      - Use ${resources.schemas.wanderbricks_schema.catalog_name} and .name

   d. Create resources/wanderbricks.lakebase.yml:
      - Lakebase Autoscaling project: PG17, 0.5-2 CU autoscaling
      - project_id: ${var.lakebase_project_id}
      - history_retention: 604800s (7 days)
      - lifecycle: prevent_destroy: true

   e. Create resources/uc_setup.job.yml:
      - Job "WanderBricks UC Setup"
      - Single task running src/notebooks/uc_setup.py
      - Base parameters: catalog, schema, lakebase_project_id (all from resource/var refs)

   f. Create src/notebooks/uc_setup.py:
      - Cell 1: %pip install --upgrade databricks-sdk + restartPython()
      - Cell 2: Widgets (catalog, schema, lakebase_project_id)
      - Cell 3: CREATE SECRET IF NOT EXISTS for lakebase_host and lakebase_db
      - Cell 4: SDK code to fetch Lakebase endpoint and ALTER SECRET with real values
      - Cell 5: Summary print

7. VALIDATE:
   - Run: databricks bundle validate --target dev
   - Fix any errors
   - Run: databricks bundle deploy --target dev
   - Verify schema exists: SHOW SCHEMAS IN hls_fde_dev LIKE 'dev_matthew_giglia_wanderbricks_ai'
   - Verify volume: SHOW VOLUMES IN hls_fde_dev.dev_matthew_giglia_wanderbricks_ai

8. COMPLETE:
   - Update fixtures/handoffs/workstream-0-status.md:
     - status: COMPLETE, completed_at, output_tables, validation: PASSED, bundle_deployed: true
     - "What Was Built" section
     - "Notes for Downstream Sessions" with variable reference patterns
   - Write session summary to fixtures/sessions/
   - Commit and push branch

IMPORTANT: Never commit to main or lesson branches directly. Use ${resources.schemas.*} refs (never raw ${var.schema}). Follow .assistant_instructions.md conventions for notebook paths (.ipynb default) and SDK notebooks (%pip + restartPython first cell).
```
