---
status: NOT_STARTED
branch:
started_at:
completed_at:
output_tables: []
validation: N/A
bundle_deployed: N/A
tests_passed: N/A
---

# Workstream 0 — Bundle Scaffold

**Status:** NOT_STARTED

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
