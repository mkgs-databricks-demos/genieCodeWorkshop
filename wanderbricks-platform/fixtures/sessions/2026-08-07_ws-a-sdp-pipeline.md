# Session Summary: WS-A SDP Pipeline (Bronze → Silver → Gold)

**Date:** 2026-08-07
**Branch:** mg-genie-wb-ws-a-pipeline

## Problems Encountered
- A `glob: include: ../src/pipelines/**` library pattern in the pipeline resource
  YAML picked up a leftover `src/pipelines/.gitkeep` placeholder file, causing
  `UNSUPPORTED_LIBRARY_FILE_TYPE` at pipeline run time (only `.py`/`.sql` are
  supported as pipeline library files).
- A single-asterisk glob (`../src/pipelines/*.py`) was rejected outright by the
  Pipelines API at deploy time (`Single asterisk glob pattern is not
  supported ... Use a double asterisk`).
- `_bronze_flow.__name__ = target_name`, added defensively after stacking
  `@dp.table` + `@dp.expect_all` decorators, raised `AttributeError: property
  '__name__' of 'DatasetOrExpectationDecoratorResult' object has no setter`
  at pipeline run time — the decorated object is not a plain function.
- `databricks bundle deploy` and `databricks bundle run` were blocked by this
  session's tool-level command allow-list until the user explicitly approved
  them in chat.
- A `createAsset` call for this very session-summary file initially resolved
  to a doubled path
  (`.../wanderbricks-platform/genieCodeWorkshop/wanderbricks-platform/fixtures/sessions/...`)
  after the active editor context moved to an unrelated file mid-session;
  retrying with a bundle-root-relative name fixed it. The stray file/folder
  was left in place with a redirect note (no delete-file tool was available).

## Root Causes
- The Lakeflow pipeline library resolver only accepts `.py`/`.sql` files and
  only supports `**` (recursive) or explicit `file:` entries for glob-based
  inclusion — directory placeholders like `.gitkeep` and single-asterisk
  globs are both unsupported.
- `@dp.table`/`@dp.expect_all` return a `DatasetOrExpectationDecoratorResult`
  wrapper object, not the original function, so post-decoration attribute
  assignment on `__name__` is unsupported and unnecessary (the table name is
  already set via the `name=` kwarg).
- `bundle deploy`/`bundle run` are mutating/execution commands gated by this
  environment's safety guardrails and require explicit human approval per
  invocation context.
- `createAsset`'s relative-path resolution appears tied to the currently
  focused editor asset rather than a fixed bundle root; when the focused
  asset changed to a file outside the bundle mid-session, a bundle-qualified
  relative name got double-prefixed.

## Decisions
- Used explicit `file:` library entries (one per source file) instead of a
  glob, since the source set is small (3 files) and fixed — this sidesteps
  both the `.gitkeep` and single-asterisk glob issues without needing to
  delete/rename any pre-existing scaffold file.
- Kept bronze ingestion metadata-driven (a single `BRONZE_TABLES` dict drives
  a loop that calls a parent `_create_bronze_table()` function per table),
  per the project's Spark Declarative Pipeline Conventions, rather than
  writing 11 near-identical `@dp.table` functions by hand.
- Scoped bronze to exactly the 11 core entities named in the task brief
  (properties, bookings, reviews, users, hosts, destinations, payments,
  countries, amenities, property_amenities, property_images) and explicitly
  did NOT add `booking_updates`, `page_views`, `customer_support_logs`,
  `clickstream`, or `employees` — those are out of WS-A's stated scope.
- `gold_host_performance`'s cancellation rate and `qualifies_superhost` flag
  are computed with the 3 of 4 Superhost criteria that are derivable from the
  in-scope bronze/silver tables; the response-rate criterion and the
  host-vs-guest cancellation split are explicitly documented as gaps pending
  a future `booking_updates` ingestion, rather than silently approximated or
  omitted without comment.
- All gold formulas were implemented to match the WanderBricks Analytics
  Handbook definitions verbatim (GBV/net revenue basis, ADR exclusions,
  occupancy rate denominator, GSS recency weights) rather than inventing
  simplified versions.

## Changes Made
- `resources/wanderbricks_pipeline.pipeline.yml` — new pipeline resource:
  serverless, `preview` channel, `ADVANCED` edition, catalog/schema wired to
  `${resources.schemas.wanderbricks_schema.*}`, 3 explicit `file:` library
  entries, `catalog_use`/`schema_use` configuration values.
- `src/pipelines/bronze.py` — new: metadata-driven bronze streaming ingestion
  for the 11 core `samples.wanderbricks` entities, `_ingested_at` column, PK
  not-null expectations via `@dp.expect_all`.
- `src/pipelines/silver.py` — new: `silver_properties`, `silver_bookings`,
  `silver_reviews`, `silver_users`, `silver_hosts`, `silver_payments`
  materialized views with a shared `_dedup()` helper, type casts, null
  handling, and expectations (`@dp.expect_all_or_drop` for hard constraints,
  `@dp.expect` for soft/monitoring-only checks).
- `src/pipelines/gold.py` — new: `gold_revenue_daily`, `gold_occupancy_monthly`,
  `gold_guest_satisfaction`, `gold_host_performance`, `gold_property_summary`
  materialized views implementing the Analytics Handbook formulas.
- `fixtures/handoffs/workstream-a-status.md` — updated `NOT_STARTED` →
  `IN_PROGRESS` → `COMPLETE`, with full output table list, validation
  results, "What Was Built", and "Notes for Downstream Sessions" for WS-B/WS-D.

## Validation Results
- `databricks bundle validate --target dev` → Validation OK
- `databricks bundle deploy --target dev` → Deployment complete
- `databricks bundle run wanderbricks_pipeline --target dev` → Update COMPLETED,
  all 22 bronze/silver/gold flows succeeded
- `bronze_bookings` row count (72,247) exactly matches `samples.wanderbricks.bookings`
- `silver_bookings` row count (72,247) matches bronze, zero duplicate `booking_id`
- `gold_revenue_daily`: 17,860 rows, `SUM(gbv)` = $9,913,945.94
- `gold_occupancy_monthly`: 18,163 distinct properties (matches total property count)
- `gold_guest_satisfaction`: `AVG(gss)` = 2.95, within the valid [1.0, 5.0] range
