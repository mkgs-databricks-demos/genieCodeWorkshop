---
status: COMPLETE
branch: mg-genie-L02-wanderbricks-scaffold
started_at: 2026-07-31T00:00:00Z
completed_at: 2026-08-04T14:30:00Z
output_tables:
  - hls_fde_dev.dev_matthew_giglia_wanderbricks_ai (schema)
  - hls_fde_dev.dev_matthew_giglia_wanderbricks_ai.reference_docs (volume)
validation: PASSED
bundle_deployed: true
tests_passed: N/A
---

# Workstream 0 — Bundle Scaffold

**Status:** COMPLETE

## Upstream Dependencies
None — this workstream creates the foundation.

## What Was Built

Created the `wanderbricks-platform` Declarative Automation Bundle with:

1. **`databricks.yml`** — Bundle definition with variables (catalog, schema, warehouse_id lookup, lakebase_project_id), resource includes, and dev target
2. **`resources/wanderbricks_schema.schema.yml`** — UC schema resource
3. **`resources/wanderbricks_volumes.volume.yml`** — Managed volume for reference docs (Analytics Handbook PDF, etc.)
4. **`resources/wanderbricks.lakebase.yml`** — Lakebase Autoscaling project (PG17, 0.5–2 CU, prevent_destroy)
5. **`resources/uc_setup.job.yml`** — Job to store Lakebase connection info as UC secrets post-deploy
6. **`src/notebooks/uc_setup.py`** — SDK notebook (install SDK → widgets → create secrets → store Lakebase endpoint)

## Notes for Downstream Sessions

**Schema:** `hls_fde_dev.dev_matthew_giglia_wanderbricks_ai` (dev mode prefixed)

**Variable references for resource YAMLs:**
- Catalog: `${resources.schemas.wanderbricks_schema.catalog_name}`
- Schema: `${resources.schemas.wanderbricks_schema.name}`
- Warehouse: `${var.warehouse_id}`
- Lakebase: `${var.lakebase_project_id}`

**Pattern for new resources:**
- Add YAML to `resources/` (auto-included via `include: - resources/*.yml`)
- Use schema refs: `${resources.schemas.wanderbricks_schema.catalog_name}` and `.name`
- Notebooks go in `src/pipelines/`, `src/notebooks/`, or `src/features/`

**Bundle commands:**
```bash
databricks bundle validate --target dev
databricks bundle deploy --target dev
databricks bundle run --target dev <resource_name>
```

## Validation Results

- Bundle validates cleanly
- Schema created in `hls_fde_dev`
- Volume created
- Lakebase project provisioned
- UC secrets created (placeholder values, updated after Lakebase endpoint ready)

## Next Steps (for human)

- [x] Review and merge branch
- [ ] Run `uc_setup` job to populate real Lakebase endpoint values
- [ ] Upload Analytics Handbook PDF to reference_docs volume
