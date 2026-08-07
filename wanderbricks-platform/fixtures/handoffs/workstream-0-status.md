---
status: COMPLETE
branch: mg-genie-L02-wanderbricks-scaffold
started_at: 2026-07-31T00:00:00Z
completed_at: 2026-07-31T00:00:00Z
output_tables: []
validation: PASSED
bundle_deployed: true
tests_passed: N/A
---

# Workstream 0 — Bundle Scaffold

**Status:** COMPLETE (done manually before orchestration was set up)

## Upstream Dependencies
None — this workstream creates the foundation.

## Expected Output
- `databricks.yml` — Bundle definition with variables, resource includes, and dev target
- `resources/wanderbricks_schema.schema.yml` — UC schema resource
- `resources/wanderbricks_volumes.volume.yml` — Managed volume for reference docs
- `resources/wanderbricks.lakebase.yml` — Lakebase Autoscaling project
- `resources/uc_setup.job.yml` — Job to store Lakebase connection info post-deploy
- `src/notebooks/uc_setup.py` — SDK notebook for UC secrets

## Validation Criteria
- Bundle validates cleanly
- Schema created in target catalog
- Volume created
- Lakebase project provisioned

## File Isolation (this workstream touches ONLY)
- `databricks.yml`
- `resources/wanderbricks_schema.schema.yml`
- `resources/wanderbricks_volumes.volume.yml`
- `resources/wanderbricks.lakebase.yml`
- `resources/uc_setup.job.yml`
- `src/notebooks/uc_setup.py`

## What Was Built
Bundle scaffold with databricks.yml (variables: catalog, schema, warehouse_id, lakebase_project_id), UC schema resource, managed volume, Lakebase autoscaling project, and UC setup job. Dev target configured for hls_fde_dev catalog.

## Notes for Downstream Sessions
- Schema reference pattern: `${resources.schemas.wanderbricks_schema.catalog_name}` and `${resources.schemas.wanderbricks_schema.name}`
- Dev target catalog: hls_fde_dev, schema prefix: wanderbricks_ai (bundle adds dev_matthew_giglia_ prefix)
- Lakebase project: wanderbricks-ai
- All resource YAMLs in resources/*.yml, included via databricks.yml
