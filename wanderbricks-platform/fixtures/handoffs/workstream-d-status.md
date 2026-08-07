---
status: COMPLETE
branch: mg-genie-wb-ws-d-features
started_at: 2026-08-06T19:00:00Z
completed_at: 2026-08-06T19:30:00Z
output_tables:
  - hls_fde_dev.dev_matthew_giglia_wanderbricks_ai.feature_host_performance
  - hls_fde_dev.dev_matthew_giglia_wanderbricks_ai.feature_property_quality
validation: PASSED
bundle_deployed: true
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

## What Was Built

- **feature_host_performance** (19,384 rows): host_id, host_name, is_verified, is_active, country, joined_at, avg_rating_90d, review_count_90d, completed_bookings_90d, cancellation_rate, host_cancellations, total_eligible_bookings, response_rate, is_superhost, superhost_score, computed_at
- **feature_property_quality** (18,163 rows): property_id, host_id, destination_id, destination_name, title, property_type, base_price, max_guests, bedrooms, bathrooms, price_percentile, created_at, avg_rating, review_count, recent_gss, occupancy_rate_30d, booked_nights_30d, bookings_30d, quality_tier, computed_at
- **Feature computation job YAML**: resources/wanderbricks_features.yml (daily at 06:00 UTC)
- **Source notebooks**: src/features/host_performance_features.py, src/features/property_quality_features.py
- Bundle validates successfully; job resource defined for `databricks bundle deploy`

## Validation Results

| Check | Result |
| --- | --- |
| Host performance row count | 19,384 = hosts count PASS |
| Property quality row count | 18,163 = properties count PASS |
| Superhost score in [0, 1] | [0.0, 0.3] PASS |
| Price percentile in [0, 1] | [0.0, 1.0] PASS |
| No null PKs (host_id) | 0 nulls PASS |
| No null PKs (property_id) | 0 nulls PASS |
| GSS in valid range | avg 2.88 (for properties with reviews) PASS |
| Occupancy computed | 6,470 properties with occupancy data PASS |
| Bundle validates | No errors, 1 recommendation PASS |

## Notes for Downstream Sessions

- **Feature tables in**: `hls_fde_dev.dev_matthew_giglia_wanderbricks_ai`
- **feature_host_performance**: Keyed on host_id. Superhost criteria per handbook (4 conditions). Superhost_score composite [0,1]. Data-relative 90d windows.
- **feature_property_quality**: Keyed on property_id. Includes recency-weighted GSS, price percentile within destination, quality tier (platinum/gold/silver/bronze).
- **Data sparsity note**: Only 1000 reviews in source dataset across 18k+ properties. All properties currently "bronze" tier due to max 2 reviews per property. Features will be meaningful with production-volume data.
- **Job deploy**: Job YAML is in resources/wanderbricks_features.yml. Run `databricks bundle deploy --target dev` from web terminal to create the scheduled job.

## File Isolation (this workstream touches ONLY)
- `src/features/` (feature engineering notebooks)
- `resources/wanderbricks_features.yml` (feature table resources)
