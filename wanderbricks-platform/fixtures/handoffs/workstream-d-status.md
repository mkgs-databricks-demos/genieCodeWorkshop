---
status: COMPLETE
branch: mg-genie-wb-ws-d-features
started_at: 2026-08-07T16:30:00Z
completed_at: 2026-08-07T17:00:00Z
output_tables:
  - feature_host_performance
  - feature_property_quality
validation: PASSED
bundle_deployed: false
tests_passed: true
---

# Workstream D — Feature Tables

**Status:** COMPLETE

## Upstream Dependencies
- WS-A COMPLETE (silver/gold tables must be populated)

## Expected Output
- Feature tables for host performance and property quality
- Feature computation job (daily schedule)
- Feature tables queryable with correct values

## Validation Criteria
- Feature tables populated with correct row counts
- Scores in valid ranges (0-1)
- No null violations in key columns
- Job deploys and validates

## File Isolation (this workstream touches ONLY)
- `src/features/` (feature engineering notebooks)
- `resources/wanderbricks_features.yml` (feature table resources)

## What Was Built

Two ML feature tables with Unity Catalog primary key constraints, computed from
the silver layer using data-relative trailing windows.

### `feature_host_performance` (19,384 rows, PK: `host_id`)
- **avg_rating_90d**: Average review rating (trailing 90 days)
- **completed_bookings_90d**: Completed booking count (trailing 90 days)
- **cancellation_rate**: Overall cancellation rate
- **response_rate**: NULL (requires `booking_updates`, not in scope)
- **is_superhost**: Boolean per Handbook 4.1 criteria 1-3
- **superhost_score**: Composite 0-1 score

### `feature_property_quality` (18,163 rows, PK: `property_id`)
- **avg_rating**: Average review rating (all time, non-deleted)
- **review_count**: Count of non-deleted reviews
- **recent_gss**: Recency-weighted GSS per Handbook 3.1
- **occupancy_rate_30d**: Occupancy rate in trailing 30 days
- **price_percentile**: PERCENT_RANK within destination
- **quality_tier**: Categorical (gold/silver/bronze/standard)

### Resource YAML
`resources/wanderbricks_features.yml` - daily job (06:00 UTC), 2 sequential tasks.

### Notebooks
- `src/features/host_performance_features.ipynb`
- `src/features/property_quality_features.ipynb`

## Validation Results
- host: 19,384 rows, superhost_score 0.0-0.81, 0 null PKs
- property: 18,163 rows, all scores valid, 0 null PKs
- Bundle validate: feature resource OK (errors only from WS-B orchestration job)
- Bundle deploy: not executed (CLI allow-list restriction)

## Notes for Downstream Sessions

### Querying
- `hls_fde_dev.dev_matthew_giglia_wanderbricks_ai.feature_host_performance`
- `hls_fde_dev.dev_matthew_giglia_wanderbricks_ai.feature_property_quality`

### Known Limitations
- `response_rate` always NULL (booking_updates not ingested)
- `is_superhost` currently always FALSE (data volume: max ~4 completed/host in 90d)
- Quality tier skewed to standard (842/18163 properties have reviews)
- Bundle deploy needed to create scheduled job
- Data-relative reference dates (2025-07-31) used since source data is historical
