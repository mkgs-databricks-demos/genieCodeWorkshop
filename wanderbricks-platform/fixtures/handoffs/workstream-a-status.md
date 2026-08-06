---
status: NOT_STARTED
branch:
started_at:
completed_at:
output_tables: []
validation: PENDING
bundle_deployed: false
tests_passed: false
---

# Workstream A — SDP Pipeline (Bronze → Silver → Gold)

**Status:** NOT_STARTED

## Upstream Dependencies
- WS-0 COMPLETE (schema must be deployed)

## Expected Output
- Full Spark Declarative Pipeline with bronze, silver, and gold layers
- Bronze: streaming tables ingesting from `samples.wanderbricks`
- Silver: cleaned/conformed tables (deduped, typed, null-handled)
- Gold: business-ready aggregates (revenue, occupancy, satisfaction)
- Pipeline resource YAML in `resources/`
- All tables populated and queryable

## Validation Criteria
- Pipeline deploys without errors
- Pipeline runs successfully (full refresh)
- Bronze tables: row counts match source (`samples.wanderbricks.*`)
- Silver tables: no nulls in PK columns, correct types
- Gold tables: at least 3 aggregate tables (revenue, occupancy, satisfaction)
- All tables in target schema

## File Isolation (this workstream touches ONLY)
- `src/pipelines/` (all pipeline notebooks)
- `fixtures/config/` (pipeline configuration)
- `resources/wanderbricks_pipeline.pipeline.yml`
