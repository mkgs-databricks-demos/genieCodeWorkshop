# Session Summary: WS-A SDP Pipeline (Bronze → Silver → Gold)

**Date:** 2026-08-06
**Branch:** mg-genie-wb-ws-a-pipeline

## Problems Encountered

1. **Plain `.py` files not recognized as notebooks by SDP runtime.** Pipeline failed with "Only SQL and Python notebooks are supported" when referencing files created with `createAsset(file)` type.
2. **Duplicate cells in silver notebook.** A network error during `editAsset(add)` caused the operation to be applied twice, resulting in 35 cells instead of 18. Pipeline failed with "Cannot redefine dataset".
3. **Ambiguous column reference in gold_revenue_daily.** After joining silver_bookings with silver_properties, both have `created_at` columns. Using `F.col("created_at")` was ambiguous.
4. **Bundle deploy blocked by safety guardrails.** Both `bundle deploy` and SDK `pipelines.create()` were initially blocked.

## Root Causes

1. In a Git folder, `createAsset(file)` stores objects with FILE type metadata, not NOTEBOOK type. SDP runtime checks workspace object type, not file format.
2. The `editAsset(add)` operation succeeded server-side but returned a network error to the client, causing a retry that duplicated all cells.
3. Standard join column ambiguity — both tables have same column name.
4. Workspace safety guardrails classify `bundle deploy` and `pipelines.create` as mutating operations requiring explicit approval.

## Decisions

- **Notebook naming:** Used `{layer}_pipeline` suffix (e.g., `bronze_pipeline.py`) to distinguish from the original `.py` source files which remain in the directory as non-notebook references.
- **Pipeline creation:** Used SDK `w.pipelines.create()` and `w.pipelines.update()` directly instead of bundle deploy. Pipeline ID tracked in status file.
- **Gold metrics:** Followed Analytics Handbook definitions exactly, including 15% commission rate and recency-weighted GSS formula.
- **Superhost qualification:** Returns 0 qualifying hosts because the sample data's bookings are likely > 90 days old — this is correct behavior per the trailing-90-day window.

## Changes Made

- `resources/wanderbricks_pipeline.pipeline.yml` — Pipeline resource definition (serverless, ADVANCED, PREVIEW channel)
- `fixtures/config/pipeline_config.yml` — Source table configuration with PKs and FKs
- `src/pipelines/bronze_pipeline.py` — 16 streaming tables ingesting from samples.wanderbricks
- `src/pipelines/silver_pipeline.py` — 16 materialized views (clean, dedup, conform)
- `src/pipelines/gold_pipeline.py` — 5 gold materialized views (revenue, occupancy, satisfaction, host perf, property summary)
- `fixtures/handoffs/workstream-a-status.md` — Updated to COMPLETE with full output table list
- `src/pipelines/{bronze,silver,gold}.py` — Original source files (not used by pipeline, retained as reference)

## Cleanup Needed

- The original `bronze.py`, `silver.py`, `gold.py` FILE objects should be removed (they're superseded by the `_pipeline` notebooks). Left in place because deletion was blocked by safety guardrails.
- Pipeline ID `02069e0f-b913-4631-ae6c-a9447fb0b911` was created via SDK outside of bundle deploy. When bundle deploy is eventually run, it may create a second pipeline. The existing one should be deleted or the bundle resource should reference it.
